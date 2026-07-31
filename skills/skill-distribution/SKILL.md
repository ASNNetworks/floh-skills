---
name: skill-distribution
description: Use when packaging, installing, publishing or sharing an Agent Skill, or when deciding how to get a SKILL.md onto someone else's machine. Covers the on-disk locations each agent client reads, plugin marketplaces for Claude Code, archive-based installs, and the mistakes that produce an install command that silently does nothing. Not for authoring the content of a skill.
---

# Distributing Agent Skills

A skill is a directory containing a `SKILL.md` file, optionally alongside `scripts/`,
`references/` and `assets/`. Every skills-compatible agent loads it the same way: **it reads a
folder on disk.** No mainstream client installs a skill from an arbitrary HTTP URL.

That single fact decides the whole distribution question. A download link is not an install
mechanism; it is a file the user still has to unpack into the right directory. Anything that
claims to be a one-command install has to put a directory somewhere the client already scans.

## Where clients look

**Claude Code** reads three locations, in precedence order (enterprise beats personal, personal
beats project):

| Scope | Path |
|-------|------|
| Personal | `~/.claude/skills/<name>/SKILL.md` |
| Project | `.claude/skills/<name>/SKILL.md` |
| Plugin | `<plugin>/skills/<name>/SKILL.md` |

Project skills also load from `.claude/skills/` in every parent directory up to the repository
root, and from nested `.claude/skills/` directories once Claude reads or edits a file inside that
subdirectory. Symlinks are followed. Changes to `SKILL.md` are picked up within the session
without a restart.

**Codex** scans, in scope order: `$CWD/.agents/skills`, `$CWD/../.agents/skills`,
`$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, and `/etc/codex/skills`. It follows symlinks
and detects changes automatically. It also ships a built-in `$skill-installer` for fetching a
skill into one of those locations.

Other clients that adopted the format use their own directories. Verify the path against that
client's current documentation before you publish an install command for it. A wrong path is
worse than an absent one: the skill simply never loads, and there is no error to notice.

## Four ways to ship, in order of user effort

### 1. Copy into a scanned directory

The lowest-tech option, and the one that works everywhere:

```bash
mkdir -p ~/.claude/skills/my-skill
cp -r my-skill/* ~/.claude/skills/my-skill/
```

Good for a personal skill or a quick share. It does not update, and nothing tracks versions.

### 2. Commit it to the repository

Put the skill in `.claude/skills/` (Claude Code) or `.agents/skills/` (Codex) and commit. Every
contributor gets it on clone, and it versions with the code that it describes. This is the right
default for anything project-specific.

Note that a project skill can carry an `allowed-tools` frontmatter field, which grants itself tool
permissions once the user accepts the workspace trust dialog. Review project skills before
trusting a repository.

### 3. A plugin marketplace (Claude Code, one command)

This is the only true one-command install. A marketplace is a git repository containing
`.claude-plugin/marketplace.json`:

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Your Name" },
  "plugins": [
    {
      "name": "my-skill",
      "source": "./",
      "skills": ["./skills/my-skill"],
      "strict": false,
      "description": "What the skill does",
      "version": "1.0.0"
    }
  ]
}
```

Users then run:

```
/plugin marketplace add owner/repo
/plugin install my-skill@my-marketplace
```

Two details that are easy to get wrong:

- **`source: "./"` plus a scoped `skills` array** is how you serve several independent plugins out
  of one flat `skills/` folder. Without the `skills` array, every entry loads every skill in the
  folder.
- **`strict: false`** means the marketplace entry is the authority, so the plugin directory needs
  no separate `.claude-plugin/plugin.json`. With the default `strict: true`, it does.

Set `version` and bump it on each release; users only receive updates when that string changes. If
you omit it in a git-hosted marketplace, every commit counts as a new version.

### 4. An archive plus a one-liner

For clients with no installer, serve a `.tar.gz` and let users pipe it straight into place:

```bash
curl -fsSL https://example.com/skills/my-skill.tar.gz | tar -xz -C ~/.claude/skills
```

Serve `.zip` as well for people who would rather click a button, and for clients whose UI takes an
uploaded archive. A zip cannot be piped into `tar -xz`, so if you offer only one format, offer the
tarball for terminals and accept that browser users get a worse experience.

## The URL trap

`/plugin marketplace add` accepts a direct URL to a `marketplace.json` file, which looks like it
lets you host a marketplace on your own website. It mostly does not work the way you expect: only
that one file is downloaded, so any plugin entry using a relative `source` path cannot resolve.

If you distribute by URL, every plugin entry must use a `github`, `url` (git) or `npm` source.
Otherwise host the marketplace in git, where relative paths resolve against the cloned copy.

## Checklist before you publish

1. `SKILL.md` has frontmatter with `name` and `description`. The description is what the agent
   sees at startup, so write it as trigger conditions, not as a summary.
2. The directory name matches what users will type. In Claude Code the command comes from the
   directory name for personal and project skills, and from the plugin namespace for plugin
   skills.
3. Any bundled script is referenced through `${CLAUDE_SKILL_DIR}` rather than a hardcoded path, so
   it resolves whether the skill is installed personally, per project, or as a plugin.
4. `marketplace.json` parses, and every path in a `skills` array exists and contains a `SKILL.md`.
5. **You ran the install yourself, on a clean machine, exactly as written.** Every step above can
   be wrong in a way that produces no error at all. An install command that has only been read is
   not a tested install command.
