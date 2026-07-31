# FLOH Skills

Agent Skills by [FLOH Solutions](https://www.floh.solutions). Portable capabilities in the open
`SKILL.md` format, usable from Claude Code, Claude.ai, Codex, Gemini CLI, Cursor, OpenCode and
other skills-compatible agents.

An Agent Skill is a folder holding a `SKILL.md` with instructions, optionally alongside scripts,
reference material and assets. Agents load the name and description at startup and read the full
instructions only when a task calls for them, so a large set of skills costs very little context
until one is actually needed.

## Catalogue

| Skill | What it does |
|-------|--------------|
| [`seo-audit`](skills/seo-audit/) | Audit a page the way a search engine reads it, with findings ranked by what actually costs you rankings. |
| [`document-extraction`](skills/document-extraction/) | Pull structured fields out of invoices, receipts and contracts, with a confidence score per field instead of a guess. |
| [`brand-voice`](skills/brand-voice/) | Turn your writing voice into rules an agent applies and a checker enforces, instead of a style guide read once. |
| [`supabase-migrations`](skills/supabase-migrations/) | The running order for Postgres migrations on self-hosted Supabase, including the step everyone forgets that fails silently. |
| [`nextjs-conventions`](skills/nextjs-conventions/) | The App Router and Tailwind v4 rules that break quietly, as a checklist your agent applies while it writes. |
| [`linkedin-carousel`](skills/linkedin-carousel/) | Turn an article into a LinkedIn carousel with a structure that works, rendered to the PDF format LinkedIn actually accepts. |
| [`skill-distribution`](skills/skill-distribution/) | Get a skill onto someone else's machine: the per-client directories, plugin marketplaces, and the mistakes that produce no error at all. |
| [`image-gen`](skills/image-gen/) | Let an agent with no image tool generate images by driving Codex or Antigravity headlessly, then judge the result itself. |

This repository is the distribution point. The browsable catalogue, with a demo and the full
source of each skill, lives at <https://www.floh.solutions/skills>.

## Install

### Claude Code (recommended)

```
/plugin marketplace add ASNNetworks/floh-skills
/plugin install <skill>@floh-skills
```

Run `/reload-plugins` afterwards to make the skill available in the current session. Update later
with `/plugin marketplace update floh-skills`.

### Claude Code or Claude.ai, single skill

```bash
git clone https://github.com/ASNNetworks/floh-skills.git /tmp/floh-skills
cp -r /tmp/floh-skills/skills/<skill> ~/.claude/skills/
```

For a project rather than your whole account, copy into `.claude/skills/` in the repository
instead and commit it.

### Codex

```bash
git clone https://github.com/ASNNetworks/floh-skills.git /tmp/floh-skills
mkdir -p ~/.agents/skills
cp -r /tmp/floh-skills/skills/<skill> ~/.agents/skills/
```

Codex also scans `$REPO_ROOT/.agents/skills` and `/etc/codex/skills`, and ships a built-in
`$skill-installer` you can point at this repository.

### One folder, four clients

`~/.agents/skills/` is read by **Codex, Cursor, Gemini CLI / Antigravity and OpenCode** alike.
Unpacking a skill there once covers all four:

```bash
git clone https://github.com/ASNNetworks/floh-skills.git /tmp/floh-skills
mkdir -p ~/.agents/skills
cp -r /tmp/floh-skills/skills/<skill> ~/.agents/skills/
```

### Other clients

Every skills-compatible client loads a folder from disk; only the directory differs. Check your
client's documentation for its skills path and copy the skill folder there. If you find the right
path for a client not listed here, a pull request adding it is welcome.

## Layout

```
floh-skills/
├── .claude-plugin/
│   └── marketplace.json     # plugin marketplace manifest, one entry per skill
├── skills/
│   └── <slug>/
│       ├── SKILL.md         # required: frontmatter + instructions
│       ├── scripts/         # optional: executable helpers
│       ├── references/      # optional: documentation loaded on demand
│       └── assets/          # optional: templates and resources
└── scripts/
    └── validate.mjs         # checks the manifest against the skills on disk
```

Each skill is exposed as its own plugin, so you install only what you want and each carries its
own version.

## Contributing

Issues and pull requests are welcome, especially install paths for clients not yet covered above.

Before opening a pull request that adds or changes a skill, run:

```bash
node scripts/validate.mjs
```

It checks that `marketplace.json` parses, that every path referenced in a `skills` array exists and
contains a `SKILL.md`, and that each `SKILL.md` carries the required `name` and `description`
frontmatter. The same check runs in CI.

## License

MIT. See [LICENSE](LICENSE).
