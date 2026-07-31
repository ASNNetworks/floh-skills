#!/usr/bin/env node
/**
 * Validates the marketplace manifest against the skills that actually exist on disk.
 *
 * Catches the failure modes that produce no error at install time and are therefore
 * invisible until a user reports that nothing happened:
 *  - marketplace.json does not parse
 *  - a plugin entry points at a skills path that does not exist
 *  - a skill directory has no SKILL.md
 *  - a SKILL.md is missing the required `name` or `description` frontmatter
 *  - a skill exists on disk but no plugin entry serves it (silently unpublished)
 */
import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const MANIFEST = join(ROOT, '.claude-plugin', 'marketplace.json');

const errors = [];
const warnings = [];

function fail(msg) {
  errors.push(msg);
}

/** Minimal YAML frontmatter reader: enough for `name` and `description` scalars. */
function readFrontmatter(md) {
  const match = md.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return null;
  const fields = {};
  for (const line of match[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z][\w-]*):\s*(.*)$/);
    if (kv) fields[kv[1]] = kv[2].trim().replace(/^["']|["']$/g, '');
  }
  return fields;
}

if (!existsSync(MANIFEST)) {
  fail('.claude-plugin/marketplace.json is missing');
} else {
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(MANIFEST, 'utf8'));
  } catch (err) {
    fail(`marketplace.json does not parse: ${err.message}`);
  }

  if (manifest) {
    if (!manifest.name) fail('marketplace.json is missing the required "name" field');
    if (!manifest.owner?.name) fail('marketplace.json is missing the required "owner.name" field');
    if (!Array.isArray(manifest.plugins)) fail('marketplace.json "plugins" must be an array');

    const served = new Set();
    const seenNames = new Set();

    for (const plugin of manifest.plugins ?? []) {
      const label = plugin.name || '<unnamed>';
      if (!plugin.name) fail('a plugin entry has no "name"');
      if (seenNames.has(plugin.name)) fail(`duplicate plugin name "${plugin.name}"`);
      seenNames.add(plugin.name);
      if (!plugin.description) warnings.push(`plugin "${label}" has no description`);
      if (!plugin.version) warnings.push(`plugin "${label}" has no version, so every commit is a new release`);

      // `source: "./"` with a scoped `skills` array is how one flat skills/ folder
      // serves several independent plugins. Without the array, every entry would
      // load every skill in the folder.
      const paths = Array.isArray(plugin.skills) ? plugin.skills : plugin.skills ? [plugin.skills] : [];
      if (plugin.source === './' && paths.length === 0) {
        fail(`plugin "${label}" uses source "./" without a scoped "skills" array, so it would load every skill in the repository`);
      }

      for (const rel of paths) {
        const dir = join(ROOT, rel);
        if (!existsSync(dir) || !statSync(dir).isDirectory()) {
          fail(`plugin "${label}" references "${rel}", which is not a directory`);
          continue;
        }
        served.add(resolve(dir));
        const skillFile = join(dir, 'SKILL.md');
        if (!existsSync(skillFile)) {
          fail(`"${rel}" has no SKILL.md`);
          continue;
        }
        const fm = readFrontmatter(readFileSync(skillFile, 'utf8'));
        if (!fm) {
          fail(`"${rel}/SKILL.md" has no YAML frontmatter block`);
          continue;
        }
        if (!fm.name) fail(`"${rel}/SKILL.md" frontmatter is missing "name"`);
        if (!fm.description) fail(`"${rel}/SKILL.md" frontmatter is missing "description"`);
      }
    }

    // A skill on disk that no entry serves is published nowhere and nobody is told.
    const skillsDir = join(ROOT, 'skills');
    if (existsSync(skillsDir)) {
      for (const entry of readdirSync(skillsDir)) {
        const dir = join(skillsDir, entry);
        if (!statSync(dir).isDirectory()) continue;
        if (!served.has(resolve(dir))) {
          fail(`skills/${entry} exists but no plugin entry serves it, so it cannot be installed`);
        }
      }
    }
  }
}

for (const w of warnings) console.warn(`warning: ${w}`);

if (errors.length) {
  for (const e of errors) console.error(`error: ${e}`);
  console.error(`\n${errors.length} problem(s) found.`);
  process.exit(1);
}

console.log('marketplace.json and the skills on disk agree.');
