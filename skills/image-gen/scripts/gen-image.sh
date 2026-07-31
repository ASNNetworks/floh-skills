#!/usr/bin/env bash
# Generate an image by driving a local coding agent that has an image tool.
#
#   gen-image.sh [--provider codex|antigravity|auto] [--name <slug>] [--dest <path>] <brief-file>
#
# Providers:
#   codex        OpenAI Codex CLI, built-in image_gen tool      -> PNG
#   antigravity  Google Antigravity CLI (agy), generate_image   -> JPEG
#   auto         codex if present, else antigravity (default)
#
# Destination (unless --dest overrides):
#   <repo-root>/claude-image-gen/<slug>-<provider>.png
# where <repo-root> is the git root of $PWD, or $PWD when not in a repo, and
# <slug> is --name or a slug derived from the first line of the brief.
#
# Never overwrites; versions to -v2, -v3. Converts format with sips when needed.

set -euo pipefail

# ---- portability shims (added for Linux; no behaviour change on macOS) -------
# This skill was authored and verified on macOS. Three things in it are macOS-only:
#   * /private/tmp does not exist on Linux, so mktemp -d there fails outright
#   * `stat -f` is BSD; GNU coreutils wants `stat -c`
#   * `sips` is macOS-only (and neither magick nor convert is guaranteed elsewhere)
# python3 is already required by the imagegen tooling, so it does the portable work.

# Scratch dir for the agent's workspace. It MUST sit inside a directory Antigravity
# trusts, or agy can stall at start on an untrusted workspace. That is why macOS used
# /private/tmp. Here we read agy's own trustedWorkspaces and pick from it, so this is
# self-configuring instead of hardcoding one platform's answer.
scratch_base() {
  if [ -n "${GEN_IMAGE_TMPDIR:-}" ]; then printf '%s\n' "$GEN_IMAGE_TMPDIR"; return; fi
  python3 - <<'PY'
import json, os, sys
settings = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
trusted = []
try:
    with open(settings) as fh:
        trusted = [os.path.abspath(os.path.expanduser(t))
                   for t in (json.load(fh).get("trustedWorkspaces") or [])]
except Exception:
    pass

def is_trusted(path):
    path = os.path.abspath(path)
    return any(path == t or path.startswith(t.rstrip("/") + "/") for t in trusted)

# Prefer a cache dir under $HOME: on this box trustedWorkspaces is ["/root"], i.e. $HOME,
# so this is covered without editing anyone's settings.
home_cache = os.path.expanduser("~/.cache/gen-image")
for candidate in (home_cache, "/private/tmp", "/tmp"):
    parent = candidate if candidate.startswith("/private") or candidate == "/tmp" else os.path.dirname(candidate)
    if candidate == home_cache:
        os.makedirs(candidate, exist_ok=True)
    elif not os.path.isdir(candidate):
        continue
    if not trusted or is_trusted(candidate):
        print(candidate)
        sys.exit(0)

# Nothing trusted was writable. Fall back and warn: codex does not care, agy might stall.
fallback = "/private/tmp" if os.path.isdir("/private/tmp") else "/tmp"
print(fallback)
sys.stderr.write(
    "warning: %s is not in Antigravity's trustedWorkspaces; agy may stall. "
    "Add it there, or set GEN_IMAGE_TMPDIR to a trusted path.\n" % fallback)
PY
}

# Newest image file under a directory. Replaces `find ... -exec stat -f` (BSD-only).
newest_image() {  # newest_image <dir> <maxdepth> [newer-than-file]
  python3 - "$@" <<'PY'
import os, sys
root = sys.argv[1]
maxdepth = int(sys.argv[2])
newer = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
cutoff = 0.0
if newer and os.path.exists(newer):
    cutoff = os.path.getmtime(newer)
exts = {".png", ".jpg", ".jpeg", ".webp"}
base = root.rstrip("/").count("/")
best = (0.0, "")
for dirpath, dirnames, filenames in os.walk(root):
    if dirpath.rstrip("/").count("/") - base >= maxdepth:
        dirnames[:] = []
    for fn in filenames:
        if os.path.splitext(fn)[1].lower() not in exts:
            continue
        path = os.path.join(dirpath, fn)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        if mtime > cutoff and mtime > best[0]:
            best = (mtime, path)
print(best[1])
PY
}

# Format conversion. sips when present (macOS), else Pillow.
img_convert() {  # img_convert <src> <dst>
  local src="$1" dst="$2" fmt
  if command -v sips >/dev/null 2>&1; then
    fmt="${dst##*.}"; [ "$fmt" = "jpg" ] && fmt="jpeg"
    if sips -s format "$fmt" "$src" --out "$dst" >/dev/null 2>&1; then return 0; fi
  fi
  python3 - "$src" "$dst" <<'PY' 2>/dev/null
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src)
if dst.lower().endswith((".jpg", ".jpeg")) and im.mode in ("RGBA", "P", "LA"):
    im = im.convert("RGB")
im.save(dst)
PY
}

# Pixel dimensions. The delivery rules require reporting these, so a missing sips must
# not mean a missing number.
img_dims() {  # img_dims <file>
  if command -v sips >/dev/null 2>&1; then
    sips -g pixelWidth -g pixelHeight "$1" 2>/dev/null | tail -2 && return 0
  fi
  python3 - "$1" <<'PY' 2>/dev/null
import sys
from PIL import Image
w, h = Image.open(sys.argv[1]).size
print("  pixelWidth: %d" % w)
print("  pixelHeight: %d" % h)
PY
}

PROVIDER="auto"; DEST=""; NAME=""
while [ $# -gt 0 ]; do
  case "$1" in
    --provider) PROVIDER="${2:-}"; shift 2 ;;
    --provider=*) PROVIDER="${1#*=}"; shift ;;
    --dest) DEST="${2:-}"; shift 2 ;;
    --dest=*) DEST="${1#*=}"; shift ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --name=*) NAME="${1#*=}"; shift ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *) break ;;
  esac
done

[ $# -ge 1 ] || { echo "usage: $0 [--provider P] [--name SLUG] [--dest PATH] <brief-file>" >&2; exit 2; }
BRIEF="$1"
[ -r "$BRIEF" ] || { echo "brief file not readable: $BRIEF" >&2; exit 2; }

# ---- first-run preflight ----------------------------------------------------
# On a machine that has never run this skill, check the setup and say exactly what is
# missing BEFORE burning two minutes of an agent's time on a run that cannot work.
# preflight.sh caches its verdict against a fingerprint of the binaries and the agy
# settings, so once it has passed the cost is a couple of stat calls per run, and it
# re-checks by itself when anything relevant changes.
#   exit 2 = no provider at all -> stop here, the guidance is already on stderr
#   exit 1 = something is off  -> warn but continue; the run may still work
if [ "${GEN_IMAGE_SKIP_PREFLIGHT:-0}" != "1" ]; then
  # Parameter expansion rather than dirname: one less binary to depend on.
  PREFLIGHT="${0%/*}/preflight.sh"
  if [ -x "$PREFLIGHT" ]; then
    "$PREFLIGHT" --quiet
    case "$?" in
      2) exit 127 ;;
      1) echo "continuing despite the warnings above" >&2 ;;
    esac
  fi
fi

CODEX_BIN="$(command -v codex 2>/dev/null || true)"
[ -x "${CODEX_BIN:-}" ] || { [ -x "$HOME/.npm-global/bin/codex" ] && CODEX_BIN="$HOME/.npm-global/bin/codex"; }
AGY_BIN="$(command -v agy 2>/dev/null || true)"
[ -x "${AGY_BIN:-}" ] || { [ -x "$HOME/.local/bin/agy" ] && AGY_BIN="$HOME/.local/bin/agy"; }

if [ "$PROVIDER" = "auto" ]; then
  if [ -n "${CODEX_BIN:-}" ]; then PROVIDER="codex"
  elif [ -n "${AGY_BIN:-}" ]; then PROVIDER="antigravity"
  else
    cat >&2 <<'EOF'
No image-capable agent CLI found. Neither is installed:

  Codex (ChatGPT images) — preferred
    npm install -g @openai/codex
    codex            # launch once and sign in with your ChatGPT account
    Image generation is the built-in image_gen tool; no OPENAI_API_KEY needed.

  Antigravity (Gemini images)
    Download the IDE from https://antigravity.google and install it
    Launch it once and sign in with your Google account
    agy install      # puts the `agy` CLI on your PATH (binary lives at ~/.local/bin/agy)

Install either one, then re-run.
EOF
    exit 127
  fi
fi

case "$PROVIDER" in
  codex) [ -n "${CODEX_BIN:-}" ] || { echo "codex not installed. Run: npm install -g @openai/codex" >&2; exit 127; } ;;
  antigravity) [ -n "${AGY_BIN:-}" ] || { echo "antigravity CLI (agy) not installed. See https://antigravity.google, then: agy install" >&2; exit 127; } ;;
  *) echo "unknown provider: $PROVIDER (use codex, antigravity, or auto)" >&2; exit 2 ;;
esac

# ---- destination ------------------------------------------------------------
if [ -z "$DEST" ]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  [ -n "$ROOT" ] || ROOT="$PWD"
  if [ -z "$NAME" ]; then
    # slug from the brief's first non-empty line: first 5 words, alnum only
    NAME="$(awk 'NF{print; exit}' "$BRIEF" \
      | tr '[:upper:]' '[:lower:]' \
      | sed -e 's/[^a-z0-9]\+/-/g' -e 's/^-//' -e 's/-$//' \
      | cut -d- -f1-5)"
    [ -n "$NAME" ] || NAME="image"
  fi
  DEST="$ROOT/claude-image-gen/${NAME}-${PROVIDER}.png"
fi

# ---- run --------------------------------------------------------------------
# /private/tmp is in Antigravity's trustedWorkspaces; $TMPDIR (/var/folders/...) may not be.
WORK="$(mktemp -d "$(scratch_base)/gen-image.XXXXXX")"
PROMPT="$WORK/prompt.txt"
LOG="$WORK/run.log"
SRC=""

echo "provider:  $PROVIDER"
echo "workspace: $WORK"
echo "running (codex ~2min, antigravity ~20s)..." >&2

if [ "$PROVIDER" = "codex" ]; then
  {
    cat "$BRIEF"
    printf '\n\n---\n'
    printf 'Use your imagegen skill (the built-in image_gen tool, not the API-key CLI fallback) to generate this as a real raster image.\n'
    printf 'Then copy your chosen final image out of $CODEX_HOME/generated_images/... into your current working directory, named exactly image.png\n'
    printf 'Do not write anywhere outside your working directory. Do not ask follow-up questions. Produce the file, report its path, and finish.\n'
  } > "$PROMPT"

  if ! "$CODEX_BIN" exec -C "$WORK" --skip-git-repo-check -s workspace-write \
       -o "$WORK/last-message.txt" - < "$PROMPT" > "$LOG" 2>&1; then
    echo "codex exec failed; tail of $LOG:" >&2; tail -30 "$LOG" >&2; exit 1
  fi
  LASTMSG="$WORK/last-message.txt"

  SRC="$WORK/image.png"
  if [ ! -f "$SRC" ]; then
    SRC="$(newest_image "$WORK" 1)"
  fi

else
  # agy headless auto-denies permission-gated tools, but generate_image needs no
  # permission. Keep it away from run_command/write_to_file and just take its path.
  {
    cat "$BRIEF"
    printf '\n\n---\n'
    printf 'Use your generate_image tool to generate this as a real raster image.\n'
    printf 'Do NOT run any shell commands and do NOT use write_to_file — those are auto-denied in headless mode and will abort the run.\n'
    printf 'After the image tool returns, output the absolute filesystem path of the generated image on a line by itself, and nothing else.\n'
  } > "$PROMPT"

  BRAIN="$HOME/.gemini/antigravity-cli/brain"
  STAMP="$WORK/.stamp"; : > "$STAMP"

  ( cd "$WORK" && "$AGY_BIN" --print-timeout 300s -p "$(cat "$PROMPT")" ) > "$LOG" 2>&1 || {
    echo "agy failed; tail of $LOG:" >&2; tail -30 "$LOG" >&2; exit 1
  }
  LASTMSG="$LOG"

  SRC="$(grep -oE '/[^ `"'"'"']+\.(jpg|jpeg|png|webp)' "$LOG" 2>/dev/null | tail -1 || true)"
  if [ -z "${SRC:-}" ] || [ ! -f "$SRC" ]; then
    SRC="$(newest_image "$BRAIN" 99 "$STAMP")"
  fi
fi

if [ -z "${SRC:-}" ] || [ ! -f "$SRC" ]; then
  echo "no image produced. Agent's output:" >&2
  tail -20 "${LASTMSG:-$LOG}" >&2 2>/dev/null || true
  echo "(full transcript: $LOG)" >&2
  exit 1
fi

# ---- deliver ----------------------------------------------------------------
mkdir -p "$(dirname "$DEST")"
if [ -e "$DEST" ]; then
  base="${DEST%.*}"; ext="${DEST##*.}"; n=2
  while [ -e "${base}-v${n}.${ext}" ]; do n=$((n+1)); done
  DEST="${base}-v${n}.${ext}"
  echo "destination existed; writing $DEST instead" >&2
fi

src_ext="$(echo "${SRC##*.}" | tr '[:upper:]' '[:lower:]')"
dst_ext="$(echo "${DEST##*.}" | tr '[:upper:]' '[:lower:]')"
[ "$src_ext" = "jpeg" ] && src_ext="jpg"
[ "$dst_ext" = "jpeg" ] && dst_ext="jpg"

if [ "$src_ext" = "$dst_ext" ]; then
  cp "$SRC" "$DEST"
else
  case "$dst_ext" in
    png|jpg|tiff|gif)
      fmt="$dst_ext"; [ "$fmt" = "jpg" ] && fmt="jpeg"
      img_convert "$SRC" "$DEST" \
        || { echo "conversion $src_ext->$dst_ext failed; copying original bytes" >&2; cp "$SRC" "$DEST"; } ;;
    *) cp "$SRC" "$DEST" ;;
  esac
fi

echo
echo "image:      $DEST"
img_dims "$DEST" || true
echo "size:       $(du -h "$DEST" | cut -f1)"
echo "source:     $SRC"
echo "transcript: $LOG"
echo
echo "--- agent's closing message ---"
tail -20 "${LASTMSG:-$LOG}" 2>/dev/null || echo "(none)"
