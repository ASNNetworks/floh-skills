---
name: image-gen
description: "Generate and edit raster images by driving a local coding-agent CLI that has an image tool — Codex (ChatGPT/OpenAI images) or Antigravity (Google Gemini images). Use whenever the user asks for an image to be generated, drawn, rendered, or made — 'generate an image of X', 'make me a picture', 'ask codex to draw Y', 'use gemini to generate Z', 'have codex picture what W looks like'. Also use when the user asks for an EXISTING image to be edited, changed, re-posed or given a variant, or for a new image matching a reference image they already have — 'make her point instead of thumbs-up', 'same character but waving', 'one more pose for this set', 'make one in this style'. Images default to <repo-root>/claude-image-gen/<name>-<provider>.png; also use this skill when the user names a different export folder or filename, such as the Desktop. Honour an explicitly named provider (codex / chatgpt / openai vs antigravity / gemini / google); default to Codex when none is named. Do NOT use for SVG/vector or code-native graphics, or for charts and data visualization (use dataviz)."
---

# Generating images through a local agent CLI

Claude has no image-generation tool. Two locally installed agent CLIs do. This skill
drives them headlessly so an image request costs one command, not an investigation.

## First run on a new machine

`gen-image.sh` runs `scripts/preflight.sh` before it does anything else, so a machine that
cannot generate an image says so in a second rather than after a two-minute run that was
never going to work.

```bash
scripts/preflight.sh            # human-readable
scripts/preflight.sh --json     # for you to parse
scripts/preflight.sh --force    # re-check after the user installs something
```

| Exit | Means | What you do |
| --- | --- | --- |
| 0 | at least one provider is installed and usable | proceed |
| 1 | installed but something is off (not signed in, untrusted workspace, no python3) | relay the warning, then proceed; it may still work |
| 2 | neither provider installed | **stop.** Give the user the install instructions it printed |

On exit 2, do **not** fall back to an SVG or a CSS drawing. That is a different deliverable
and the user did not ask for it. Say which providers you looked for and where.

**How "first run" is detected.** State lives at `~/.cache/floh-image-gen/preflight.json`. No
file means this skill has never run here, which is exactly when to check everything and walk
the user through setup. When the file is there, preflight compares a fingerprint of the
environment (each binary's path, size and mtime, plus the mtime of the Antigravity settings
and of the Codex auth file) against the stored one. Unchanged means every probe is skipped,
so the steady-state cost is a few `stat` calls. Changed means a re-check, because an
upgrade, a reinstall or an edited settings file is precisely when a cached "it worked once"
becomes a lie.

Set `GEN_IMAGE_SKIP_PREFLIGHT=1` to bypass it, and `GEN_IMAGE_STATE_DIR` to move the state.

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

**The original always lands here, even when the deliverable doesn't.** Often the generated
image is raw material rather than the finished asset: it gets cropped, rescaled, converted,
and dropped into the project somewhere specific. When that happens the derived asset goes to
its project path *and* the untouched generator output still goes to `claude-image-gen/`.
Do not leave it in a scratch directory — that is gone at the end of the session, and the
generation is not reproducible.

Keep both halves when post-processing happened:

| File | What |
| --- | --- |
| `<name>-<provider>.png` | the output as the generator delivered it |
| `<name>-<provider>-chroma.png` | the pre-chroma-key version, when a green screen was used |
| `<name>-vN-rejected-<provider>.png` | earlier attempts, when it took more than one round |

The full-resolution original is typically 3–5× the size the project ends up using. Without
it, a later re-crop, a different scale, or a different matte setting means re-generating —
and the model will not draw the same image twice.

## The fast path

```bash
~/.claude/skills/image-gen/scripts/gen-image.sh \
  [--provider codex|antigravity] [--name <slug>] [--dest <path>] \
  [--edit <image>] [--ref <image>]... [--file <path>]... <brief-file>
```

`--edit` changes one thing about an existing image and carries the rest over. `--ref` supplies
style/character references for a fresh generation and repeats. Both stage their inputs inside
the agent's workspace, flattening alpha onto white on the way in — hand a model a transparent
cutout and it may composite it on black and faithfully match the silhouette. In edit mode the
default slug becomes `<source-name>-edit`.

`--file` stages a **project** file the agent reads for itself — a component, a token sheet, a
copy deck. Repeatable. See *Generating from your project* below for when to reach for it.

```bash
# one more pose for an existing set — prefer this over describing the character
gen-image.sh --edit avatar-thumbs-up.png --name avatar-pointing brief.txt

# fresh image, but in the house style
gen-image.sh --ref master.png --ref hands.png --name avatar-waving brief.txt

# a mockup that has to agree with the product's real palette and vocabulary
gen-image.sh --file src/theme/tokens.ts --file docs/brand.md --name dashboard-mockup brief.txt
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
- **`read_file(/abs/dir)`** is what image-viewing needs, and the kind is `read_file` — not the
  `read` listed above, which came from strings in the binary rather than from a live denial.
  Without it, asking agy to look at a local image dies with *"a tool required the `read_file`
  permission that headless mode cannot prompt for"*. With it, agy reads and describes the
  image correctly (verified 2026-07-31).

**Set this up once, before you need it.** Reference-image work is silently unavailable without
it, and the failure arrives at the end of a run rather than the start. `preflight.sh` reports a
`note` when the rule is missing (it does not fail the check — plain generation is unaffected).
The fix, in `~/.gemini/antigravity-cli/settings.json`:

```json
{
  "trustedWorkspaces": ["/root"],
  "permissions": {
    "allow": ["read_file(/root/.cache/gen-image)"]
  }
}
```

Point the target at the same directory `scratch_base()` picks — `~/.cache/gen-image` unless
`GEN_IMAGE_TMPDIR` overrides it. `read_file` is recursive over a directory, like `write_file`.
Do not widen it to the home directory to save a thought: the scratch dir is where references
get copied, and nothing outside it needs reading.
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

## Generating from your project

The agent does **not** see your repository. It runs in a throwaway workspace with its own
working directory, and the only things in there are the ones this script puts there. That is
deliberate: an image agent that can wander a codebase spends turns navigating instead of
drawing, and on a shared box it is reading things nobody scoped.

So project context arrives through exactly three channels, and choosing the right one is most
of the work:

| Channel | Carries | Use it for |
|---|---|---|
| the brief | prose you wrote | intent, mood, framing, what to avoid |
| `--ref` / `--edit` | an image, as a **visual input to the generator** | style, character, house look |
| `--file` | a file the agent **reads for itself** | the ground truth it must not get wrong |

**Reach for `--file` when the truth is structured and exact.** Paraphrasing a token sheet into
a brief loses the hex values; paraphrasing a component loses the hierarchy; paraphrasing a copy
deck loses the wording. Hand over the file and none of that is lost in the retelling.

**Name the files; do not hand over the repo.** By the time you are generating an image you have
already read the code, so picking three to six files is sharper than any exploration the
sub-agent could do — and cheaper, since it pays no tokens to find them and cannot wander into
something irrelevant on the way.

Mechanically, each file is **copied** into `context/` inside the workspace under its own
basename (colliding names get `-2`, `-3`), and the brief lists every one with the absolute path
it came from, so the agent knows what it is looking at. Copying rather than granting access is
what makes "these files and no others" a property of the workspace instead of a permission rule
somebody has to widen to your project. Codex reads them with its own tools under
`workspace-write`; Antigravity uses `read_file`, covered by the **same allow-rule the reference
images already need** — one rule, because both live in the scratch dir.

It is not a substitute for `--ref`. A reference image is a visual input to the generator itself;
a staged file is text the agent reasons over before it writes its prompt. An image passed to
`--file` gets a warning saying so.

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
  `~/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py`. Its flags are
  **`--input` and `--out`** — `--output` exits 2 with a usage error. Add `--despill
  --spill-cleanup` so the key colour does not survive in the antialiased outline. Use Codex,
  not Antigravity: JPEG output leaves a green fringe the key cannot remove (see above). True
  native transparency needs Codex's API-key CLI fallback — ask the user before going there.

## Matching an existing set of assets

The common real request is not "draw me a picture" but "draw another one of these" — one more
pose for a mascot, one more icon for a set, one more illustration in a house style. Reaching
for the fast path here produces something that is fine on its own and obviously foreign next
to its siblings.

**Prefer editing an existing member of the set over generating a new one from references.**
This is the strongest lever available and it is easy to miss, because there is no tool that
announces it. Verified 2026-07-31: handed one pose and asked to change only the raised hand,
Codex returned an image whose face, glasses, beard, shirt folds, buttons, trousers and crop
were carried over intact — far closer than anything a reference-guided fresh generation
produced in the same session.

**There is no `image_edit` tool.** Confirmed against the binary (only `image_gen`, `imagegen`
and `view_image` appear) and confirmed by Codex itself: *"Separate `image_edit` tool: No."*
Editing runs through the same `image_gen` tool with no `mode` parameter — the source image is
supplied from conversation context via `num_last_images_to_include: 1`. So the flow is
`view_image` the source, then ask for the edit.

**Do not promise pixel preservation.** It is a redraw, and the numbers say so plainly:

| Difference threshold | Pixels changed |
| --- | --- |
| any (>0) | 99.26% |
| >4/255 | 65.89% |
| >16/255 | 6.13% |
| >48/255 | 3.56% |

Virtually every pixel moves a little; only ~6% move enough to see. That is excellent for
continuing a set and useless if someone needs the original bytes back — say which one you are
offering. Caveat on the measurement: the source here was itself Codex-generated, so it was
in-distribution. Expect a weaker hold when editing artwork from elsewhere.

**Both providers can see local files — by different routes.** Verified 2026-07-31, both ends
tested against the same reference:

| | Codex | Antigravity |
| --- | --- | --- |
| Mechanism | `view_image` loads the file into its **context**, then it writes its own prompt from what it saw | `generate_image` takes an **`ImagePaths` parameter** — the file is a direct visual input to the generator |
| Headless gate | none | needs `read_file(<dir>)` in `permissions.allow`, else auto-denied |
| Output format | PNG | **JPEG** — see below |

Codex genuinely reasons over the reference: given a master and a rejected attempt it
volunteered *"the master uses chunky, near-black contour lines and simplified flat shapes; the
failed version drifted toward polished portrait rendering"*. Antigravity's route is more
direct — the reference reaches the image model itself rather than a description of it — and it
produced a well-matched pose in ~40 s against Codex's ~2.5 min.

**But pick Codex when the result needs a transparent background.** Antigravity only emits
JPEG, and JPEG bleeds the key colour into every edge, so the chroma key cannot separate it.
Measured on the same green-screen brief through both:

| | Residual green on the figure | Alpha edge |
| --- | --- | --- |
| Codex (PNG) | 0 px (0.00%) | 8036 antialiased pixels |
| Antigravity (JPEG) | 32 986 px (6.36%) | 0 partial pixels — hard, aliased |

That is a visible green fringe around every inked outline, not a statistical artifact. For a
cutout, use Codex. For a style-matched image that stays on an opaque background, Antigravity
is the faster route and its reference mechanism is the stronger one.

The recipe:

1. **Copy 2–4 references into the agent's workspace** (`$WORK/refs/`) and name them by role,
   not by filename — the master for style, one for the specific feature you need (how hands
   are drawn, how a shadow falls), one spare. Flatten transparency onto white first; a
   transparent PNG viewed against a dark background reads as a silhouette.
2. **Name one file as the master** and say the new image must look like it came off the same
   sheet: same hand, same marker, same palette, same proportions.
3. **Tell it to `view_image` all of them before drawing.** Being in the workspace is not the
   same as being in its context.
4. **Give hex values, sampled from the reference.** Read the dominant colours out of the
   actual file rather than describing them. "Mid grey shirt" drifts to white; `#a8adb2` does not.
5. **Spell out the invariants** — everything that must NOT change — and separately the one
   thing that does. Character, clothing, crop and framing are invariants; pose and expression
   are the change.

**When the first attempt drifts, retry with the failure as evidence.** Do not just re-run the
same brief. Write the rejected image into `refs/` labelled as a negative example, and open the
retry with a plain list of what went wrong: outlines too thin, fabric too pale, too much
headroom, head too narrow. Measured on this exact loop, one such retry went from off-style to
usable, where a plain re-roll had no reason to.

**Watch what the downstream normalizer keys on.** If the set is post-processed by a script,
read that script first — it may centre on the head, plant a baseline, or scale to a fixed
silhouette height. A raised hand next to the head skews a head-centring calculation, so the
brief should place the hand at shoulder height. Constraints like that belong in the brief, not
in a later fix-up.

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
- **Resample once, from the original.** When the asset needs to be smaller, go straight from
  the full-resolution generator output to the final size in a single step. Scaling down to fit
  some intermediate convention and then letting a downstream script scale back up throws away
  detail you already had — measured at ~13% less edge energy than a single downscale, and
  plainly visible on inked outlines and small features like glasses or teeth.
- Report the absolute final path, pixel dimensions (`sips -g pixelWidth -g pixelHeight`),
  and an honest description of what the image actually shows.
- Copy only what was asked for. Mention side artifacts and offer them; don't deposit them.
  **The untouched original is not a side artifact** — it always goes to `claude-image-gen/`,
  see above.

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
