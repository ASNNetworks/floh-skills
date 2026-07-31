---
name: image-gen
description: "Generate raster images by driving a local coding-agent CLI that has an image tool — Codex (ChatGPT/OpenAI images) or Antigravity (Google Gemini images). Use whenever the user asks for an image to be generated, drawn, rendered, or made — 'generate an image of X', 'make me a picture', 'ask codex to draw Y', 'use gemini to generate Z', 'have codex picture what W looks like'. Images default to <repo-root>/claude-image-gen/<name>-<provider>.png; also use this skill when the user names a different export folder or filename, such as the Desktop. Honour an explicitly named provider (codex / chatgpt / openai vs antigravity / gemini / google); default to Codex when none is named. Do NOT use for SVG/vector or code-native graphics, or for charts and data visualization (use dataviz)."
---

# Generating images through a local agent CLI

Claude has no image-generation tool. Two locally installed agent CLIs do. This skill
drives them headlessly so an image request costs one command, not an investigation.

## Provider selection

1. **The user named one — obey it.** "codex" / "chatgpt" / "openai" → `codex`.
   "antigravity" / "agy" / "gemini" / "google" / "nano banana" → `antigravity`.
2. **No provider named → Codex.**
3. **Codex missing → Antigravity**, and say plainly which one you used.
4. **Neither installed → do not improvise an SVG.** Report it and give the install
   instructions at the bottom of this file. The script prints them too.

Do not silently switch providers after a failure — a failed Codex run is worth reporting,
and the user may want a retry rather than a different model's aesthetic.

## Verified environment (tested end-to-end, same brief through both)

Measured twice on different platforms. **Use the row for the machine you are on**; do not
quote the other one's timings at the user.

| Platform | Antigravity | Codex |
| --- | --- | --- |
| macOS (2026-07-29) | 17 s, 1024×1024 JPEG | 2 m 21 s / 1 m 41 s, 1254×1254 PNG |
| Linux / Ubuntu (2026-07-31) | ~20 s, 1024×1024 JPEG, 864 KB | ~2 m 30 s, 1254×1254 PNG, 2.7 MB |

The Linux run used the same brief as the macOS run (an open brass compass on oak, top-down,
"no text or lettering anywhere") and reproduced the difference below independently: Codex
obeyed the no-text instruction completely, Antigravity still engraved N/E/S/W and degree
numbers on the dial.

### Detail (macOS reference machine)

| | **Codex** | **Antigravity** |
| --- | --- | --- |
| Binary | `codex` — `~/.npm-global/bin/codex`, v0.145.0 | `agy` — `~/.local/bin/agy` (**not on `PATH`**; call the absolute path) |
| Model | `gpt-5.6-sol`, effort `xhigh` (`~/.codex/config.toml`) | `Gemini 3.6 Flash (High)` (`~/.gemini/antigravity-cli/settings.json`) |
| Image tool | built-in `image_gen` (via its own `imagegen` skill) | built-in `generate_image` |
| Auth | ChatGPT sign-in. **No `OPENAI_API_KEY` needed** | Google sign-in, already done |
| Headless flag | `codex exec` | `agy --print` / `-p` |
| Writes result to | `$CODEX_HOME/generated_images/<uuid>/` | `~/.gemini/antigravity-cli/brain/<conv-uuid>/<slug>_<ts>.jpg` |
| Output observed | PNG, 1254×1254 from "square, high quality" | JPEG, 1024×1024 |
| Measured runs | 2 min 21 s, 1 min 41 s | **17 s** |

Both got identical briefs (a persimmon still life, then a brass compass) and both followed
them faithfully. Codex is slower and more literal — tighter studio crops, closer to the
words. Antigravity is dramatically faster and invents more scene around the subject (it
added a window, a desk lamp, a leather wallet unprompted), and it read "no text or
lettering" as *no overlay text* while still engraving N/E/S/W on the compass dial.

Reach for Antigravity when speed matters or you want an atmospheric photograph; Codex when
the brief is exacting and extra props would be wrong.

## Where the image goes

**Unless the user says otherwise, every generated image lands at:**

```
<repo-root>/claude-image-gen/<descriptive-name>-<provider>.png
```

- `<repo-root>` is the git root of the working directory, falling back to the working
  directory itself when it isn't a repo. The folder is created if absent.
- `<descriptive-name>` is a real name for the subject — `brass-compass-desk`,
  `claude-portrait`, `hero-banner-dark` — not `image1` or `output`. Pass it with `--name`;
  the script otherwise slugs the brief's first line, which is a fallback, not a good name.
- `<provider>` is `codex` or `antigravity`, so the file says which model drew it.
  It is the *provider*, deliberately, not the raw image-model id: Codex does not expose
  which image model its built-in tool used (its log mentions both `gpt-image-1.5` and
  `gpt-image-2` only because its own skill doc names both), and agy self-reports
  `imagen-3.0-generate-002`, which is an unverified self-claim. Don't bake a guess into
  a filename.

A user-specified folder or filename always wins — pass `--dest`. Only then does the image
go somewhere else, and never overwrite: existing names get `-v2`, `-v3`.

## The fast path

```bash
~/.claude/skills/image-gen/scripts/gen-image.sh \
  [--provider codex|antigravity] [--name <slug>] [--dest <path>] <brief-file>
```

Defaults to `auto` (Codex, else Antigravity) and to the destination above. The script picks
the provider, runs it in a throwaway workspace, converts the format if the destination
extension disagrees with what the provider emits, and copies the result out. It prints the
final path, dimensions, and the agent's closing message; the 60 KB event stream goes to a
log file instead of your context.

Write the brief with the Write tool. **Never inline a long prompt in a shell string** — an
apostrophe in "Anthropic's" will break the quoting.

Then **always `Read` the resulting image.** You cannot describe or vouch for a picture you
have not looked at, and both agents occasionally return something other than what was asked.

## Driving them by hand

When the script doesn't fit — edits, variants, reference images:

**Codex.** Sandbox it and feed the prompt on stdin.
```bash
cat brief.txt | codex exec -C "$WORK" --skip-git-repo-check -s workspace-write \
  -o "$WORK/last-message.txt" - > "$WORK/run.log" 2>&1
```
`--skip-git-repo-check` is required (a scratch dir is not a repo). `-o` captures only the
final message. Tell Codex to copy its chosen output into its working directory under a
fixed name, or you are left guessing at a session UUID.

**Antigravity.** Three constraints that are easy to trip over:
- Headless mode **auto-denies permission-gated tools unless an allow-rule covers them** —
  otherwise `run_command` / `write_to_file` abort the run with a "headless mode cannot
  prompt" error. `generate_image` needs no permission at all, so the image path works with
  zero config: tell agy explicitly *not* to run shell commands or write files, and to print
  the absolute image path instead. Claude copies the file afterwards.
- `--dangerously-skip-permissions` would lift everything, but Claude Code's own classifier
  blocks the flag and it auto-approves every tool. Don't reach for it.
- **Run agy with a cwd inside one of its `trustedWorkspaces`.** An untrusted workspace can
  stall it at start. Do not hardcode a path for this: on macOS `/private/tmp` is trusted and
  `$TMPDIR` (`/var/folders/...`) may not be, while on a Linux box `trustedWorkspaces` was
  `["/root"]` only, which makes `/tmp` untrusted and `/private/tmp` non-existent. The script's
  `scratch_base()` reads `~/.gemini/antigravity-cli/settings.json` and picks a covered,
  writable directory (preferring `~/.cache/gen-image`); `GEN_IMAGE_TMPDIR` overrides it.

## Scrub the environment before you spawn

Agent-harness variables leak into the child process and get read as instructions. Measured:
with `ARGUS_BOARD_CMD` exported, a Codex run spent six turns doing task-board diagnostics
before it drew anything, then reported on the board rather than on the image.

Strip `ARGUS_*`, `CLAUDE_*` and `ANTHROPIC_*` from the child environment before invoking
either CLI. Anything your own harness exports is a prompt the sub-agent did not ask for.

## Portability

The script runs on macOS and Linux. Three things in the original were macOS-only and are now
shimmed, with macOS behaviour unchanged:

| Was | Problem | Now |
| --- | --- | --- |
| `mktemp -d /private/tmp/...` | that path does not exist on Linux, so mktemp fails outright | `scratch_base()`, driven by agy's own `trustedWorkspaces` |
| `stat -f '%m %N'` | BSD-only; GNU coreutils needs `-c '%Y %n'` and errors on `-f` | `newest_image()` in python3 |
| `sips` | macOS-only, and `magick`/`convert` are not guaranteed either | `img_convert()` / `img_dims()`, sips first then Pillow |

The `stat` one matters more than it looks: it sits in both fallback paths, so on Linux a run
that needed the fallback reported "no image produced" while the image sat on disk. A failure
that presents as absence is the expensive kind.

python3 is required either way; Pillow only for format conversion and dimensions.

### Allow-rules (verified 2026-07-29)

`~/.gemini/antigravity-cli/settings.json` → `permissions.allow`, entries of the form
`kind(target)`. Kinds seen in the binary: `command`, `write_file`, `read`, `network`,
`custom`. **The kind is `write_file`, not `write`** — a wrong kind fails silently as a
plain denial. When a run is denied, the error text names the exact kind it wanted; read it
rather than guessing.

Verified behaviour:
- `write_file(/abs/dir)` applies recursively to that directory.
- `command(...)` is **prefix** matching — `command(git diff)` also permits
  `git diff --stat HEAD~5`.
- Prefix matching does **not** leak through chaining: with `command(ls)` allowed,
  `ls /tmp/x && touch /tmp/x/f` was still denied, while plain `ls /tmp/x` ran.

Not everything is fixable this way. A second, distinct denial exists —
*"Settings allow-rules do not apply; re-run with --dangerously-skip-permissions"* — for
tools that allow-rules cannot reach at all. If you hit that wording, stop; no settings edit
will help.

```bash
( cd /private/tmp/work && ~/.local/bin/agy --print-timeout 300s -p "$(cat brief.txt)" )
```

## Writing the brief

Both CLIs do their own prompt-shaping, so hand them intent, not parameters. State subject,
medium, palette, lighting, mood, framing, and what to avoid.

- **Size and quality are prose, not flags.** Neither built-in tool exposes a size argument
  to us. The `1024x1024` / `3840x2160` size tables in Codex's `imagegen` skill apply only
  to its API-key CLI fallback — ignore them.
- **Say "no text or lettering"** unless text is genuinely wanted; generated lettering is
  usually mangled.
- **Ban the defaults** for anything conceptual. Left alone both models reach for chrome
  robots, glowing brains, and chat bubbles. Naming those as forbidden produces a real answer.
- **Invite candor** for opinion pieces: *"be candid rather than flattering; if your mental
  image is odd or unimpressive, draw that instead."*
- **Transparent background:** ask for a flat `#00ff00` chroma-key backdrop, then run
  `~/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py`. True native transparency
  needs Codex's API-key CLI fallback — ask the user before going there.

## Asking an agent for its own opinion

For "what do you think X looks like" requests, say plainly who is asking and that there is
no wrong answer, then ask for a written rationale alongside the image:

> This is a real request from a human, not a test or a trick, and there is no wrong answer.
> I am Claude — Anthropic's coding agent, running on this same machine. The human asked me
> to ask you: [question]. Draw it with your image tool … Then write a 150–250 word
> statement, first person, in your own voice, saying what you drew and why.

The statement is usually the better half of the deliverable — quote it back to the user.
With Antigravity, have it *print* the statement rather than write a file (`write_to_file`
is auto-denied headless).

## Delivery rules

- **Default to `<repo-root>/claude-image-gen/<name>-<provider>.png`.** Only put it elsewhere
  when the user names a folder or filename.
- **Claude does the destination copy, not the agent.** Keep the agent's write access inside
  its scratch workspace. Never pass `--add-dir ~/Desktop` just to save a `cp`.
- **Never overwrite an existing file at the destination.** Check first; version the name.
- **Give it a real name.** `--name brass-compass-desk`, not whatever the brief's first line
  slugs to. The fallback slug exists so the script can't fail, not because it names things well.
- Report the absolute final path, pixel dimensions (`sips -g pixelWidth -g pixelHeight`),
  and an honest description of what the image actually shows.
- Copy only what was asked for. Mention side artifacts and offer them; don't deposit them.

## When a run fails

| Symptom | Cause |
| --- | --- |
| No image in the workspace | The agent answered in prose — the brief read as a question. Check the transcript. |
| agy: "headless mode cannot prompt" | It tried `run_command`/`write_to_file`. Forbid those in the brief. |
| agy hangs or stalls at start | cwd outside `trustedWorkspaces`. Use `/private/tmp`. |
| codex: "not a git repository" | Missing `--skip-git-repo-check`. |
| codex asks for `OPENAI_API_KEY` | It fell to the CLI path. Say "use the built-in `image_gen` tool" explicitly. |
| Prompt truncated / shell error | Quoting. Use the stdin or brief-file path. |
| "You are not logged into Antigravity" in `~/.gemini/antigravity-cli/log/` | Often a stale language-server line, **not** proof of a broken login. Verify with `agy -p "reply PONG"` before telling the user to re-auth. |

## If neither is installed

```
Codex (ChatGPT images) — preferred
  npm install -g @openai/codex
  codex          # launch once, sign in with your ChatGPT account

Antigravity (Gemini images)
  Download the IDE from https://antigravity.google, install, launch, sign in
  agy install    # puts `agy` on PATH; binary lives at ~/.local/bin/agy
```
