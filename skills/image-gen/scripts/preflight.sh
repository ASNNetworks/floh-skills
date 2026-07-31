#!/usr/bin/env bash
# Preflight for the image-gen skill: is this machine actually able to generate an image,
# and if not, exactly what does the user have to install or sign into?
#
#   preflight.sh              human-readable report
#   preflight.sh --json       machine-readable, for the calling agent
#   preflight.sh --force      re-run every check, ignoring the cached result
#   preflight.sh --quiet      print nothing when everything is fine (exit code only)
#
# Exit codes:
#   0  at least one provider is installed and looks usable
#   1  a provider is installed but something is wrong (auth, python3, workspace trust)
#   2  no provider installed at all
#
# FIRST-RUN DETECTION. State lives in $STATE_DIR/preflight.json. Absent means this skill has
# never run here, which is the moment to check everything and guide setup. Present means we
# compare a cheap fingerprint of the environment (binary path + size + mtime, plus the agy
# settings mtime) against the stored one. Unchanged, we skip every probe, so the steady-state
# cost is a handful of stat calls. Changed, we re-check: a reinstall, an upgrade or an edited
# settings file are exactly the moments a stale "it worked once" answer becomes a lie.

set -uo pipefail

JSON=0; FORCE=0; QUIET=0
for arg in "$@"; do
  case "$arg" in
    --json) JSON=1 ;;
    --force) FORCE=1 ;;
    --quiet|-q) QUIET=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
  esac
done

STATE_DIR="${GEN_IMAGE_STATE_DIR:-$HOME/.cache/floh-image-gen}"
STATE_FILE="$STATE_DIR/preflight.json"

CODEX_BIN="$(command -v codex 2>/dev/null || true)"
[ -n "$CODEX_BIN" ] || { [ -x "$HOME/.npm-global/bin/codex" ] && CODEX_BIN="$HOME/.npm-global/bin/codex"; }
AGY_BIN="$(command -v agy 2>/dev/null || true)"
[ -n "$AGY_BIN" ] || { [ -x "$HOME/.local/bin/agy" ] && AGY_BIN="$HOME/.local/bin/agy"; }
AGY_SETTINGS="$HOME/.gemini/antigravity-cli/settings.json"

# ---- fingerprint ------------------------------------------------------------
# stat only. No process is spawned, so the cached path stays effectively free.
fingerprint() {
  python3 - "$CODEX_BIN" "$AGY_BIN" "$AGY_SETTINGS" "$HOME/.codex/auth.json" <<'PY'
import hashlib, os, sys
h = hashlib.sha256()
for path in sys.argv[1:]:
    if path and os.path.exists(path):
        st = os.stat(path)
        h.update(f"{path}:{st.st_size}:{int(st.st_mtime)}".encode())
    else:
        h.update(f"{path}:absent".encode())
h.update(f"py{sys.version_info.major}.{sys.version_info.minor}".encode())
print(h.hexdigest()[:24])
PY
}

FP="$(fingerprint 2>/dev/null || echo unknown)"

if [ "$FORCE" -eq 0 ] && [ -f "$STATE_FILE" ]; then
  CACHED="$(python3 -c "
import json,sys
try:
    d=json.load(open('$STATE_FILE'))
    print(d.get('fingerprint',''), d.get('status',''))
except Exception:
    print('', '')
" 2>/dev/null)"
  CACHED_FP="${CACHED%% *}"; CACHED_STATUS="${CACHED##* }"
  if [ -n "$CACHED_FP" ] && [ "$CACHED_FP" = "$FP" ] && [ "$CACHED_STATUS" = "ok" ]; then
    [ "$JSON" -eq 1 ] && cat "$STATE_FILE"
    exit 0
  fi
fi

FIRST_RUN=0
[ -f "$STATE_FILE" ] || FIRST_RUN=1

# ---- checks -----------------------------------------------------------------
problems=(); notes=(); providers=()

if [ -n "$CODEX_BIN" ]; then
  cver="$("$CODEX_BIN" --version 2>/dev/null | head -1 | tr -d '\r')"
  if [ -f "$HOME/.codex/auth.json" ]; then
    providers+=("codex:ok:${cver:-unknown}")
  else
    providers+=("codex:unauthenticated:${cver:-unknown}")
    problems+=("Codex is installed but not signed in. Run: codex   (then sign in with your ChatGPT account). No OPENAI_API_KEY is needed.")
  fi
else
  providers+=("codex:missing:")
fi

if [ -n "$AGY_BIN" ]; then
  aver="$("$AGY_BIN" --version 2>/dev/null | head -1 | tr -d '\r')"
  if [ -f "$AGY_SETTINGS" ]; then
    providers+=("antigravity:ok:${aver:-unknown}")
  else
    providers+=("antigravity:unconfigured:${aver:-unknown}")
    problems+=("The agy CLI is present but $AGY_SETTINGS does not exist, so it has probably never been launched. Open the Antigravity IDE once and sign in with your Google account.")
  fi
else
  providers+=("antigravity:missing:")
fi

# Workspace trust. This is the failure that presents as a hang rather than an error, so it
# is worth checking before a run rather than diagnosing after one.
TRUST_NOTE=""
if [ -n "$AGY_BIN" ] && [ -f "$AGY_SETTINGS" ]; then
  TRUST_NOTE="$(python3 - "$AGY_SETTINGS" "$HOME/.cache/gen-image" <<'PY'
import json, os, sys
settings, candidate = sys.argv[1], sys.argv[2]
try:
    trusted = [os.path.abspath(os.path.expanduser(t))
               for t in (json.load(open(settings)).get("trustedWorkspaces") or [])]
except Exception:
    print("could not read trustedWorkspaces"); sys.exit(0)
if not trusted:
    print("trustedWorkspaces is empty; agy may stall on any workspace"); sys.exit(0)
c = os.path.abspath(candidate)
if any(c == t or c.startswith(t.rstrip("/") + "/") for t in trusted):
    print("")
else:
    print("the scratch dir %s is not covered by trustedWorkspaces (%s); "
          "agy can stall. Add it there or set GEN_IMAGE_TMPDIR to a covered path."
          % (candidate, ", ".join(trusted)))
PY
)"
  [ -n "$TRUST_NOTE" ] && problems+=("$TRUST_NOTE")

  # Reference-image work needs a read_file allow-rule: headless agy cannot prompt for it, so
  # without one, asking it to look at a local image is auto-denied. Plain generation still
  # works, so this is a note rather than a problem.
  READ_NOTE="$(python3 - "$AGY_SETTINGS" "$HOME/.cache/gen-image" <<'PY'
import json, os, sys
settings, candidate = sys.argv[1], sys.argv[2]
try:
    allow = ((json.load(open(settings)).get("permissions") or {}).get("allow") or [])
except Exception:
    sys.exit(0)
c = os.path.abspath(candidate)
for rule in allow:
    if not rule.startswith("read_file("):
        continue
    t = os.path.abspath(os.path.expanduser(rule[len("read_file("):].rstrip(")")))
    if c == t or c.startswith(t.rstrip("/") + "/"):
        sys.exit(0)
print('agy has no read_file allow-rule covering %s, so it cannot view reference images '
      'headlessly (plain generation is unaffected). Add to %s: '
      '"permissions": {"allow": ["read_file(%s)"]}' % (candidate, settings, candidate))
PY
)"
  [ -n "$READ_NOTE" ] && notes+=("$READ_NOTE")
fi

command -v python3 >/dev/null 2>&1 || problems+=("python3 is not on PATH. The script needs it for image discovery and for reporting dimensions.")

PILLOW="no"
python3 -c "import PIL" 2>/dev/null && PILLOW="yes"
if [ "$PILLOW" = "no" ] && ! command -v sips >/dev/null 2>&1; then
  notes+=("Neither sips nor Pillow is available, so format conversion and pixel dimensions are unavailable. Install with: python3 -m pip install Pillow")
fi

HAVE_PROVIDER=0
case " ${providers[*]} " in *":ok:"*) HAVE_PROVIDER=1 ;; esac

if [ "$HAVE_PROVIDER" -eq 1 ] && [ ${#problems[@]} -eq 0 ]; then
  STATUS="ok"; CODE=0
elif [ -z "$CODEX_BIN" ] && [ -z "$AGY_BIN" ]; then
  STATUS="no-provider"; CODE=2
else
  STATUS="degraded"; CODE=1
fi

# ---- persist ----------------------------------------------------------------
mkdir -p "$STATE_DIR" 2>/dev/null
python3 - "$STATE_FILE" "$FP" "$STATUS" "$PILLOW" "${providers[@]}" <<'PY' 2>/dev/null
import json, sys, time
state_file, fp, status, pillow = sys.argv[1:5]
providers = {}
for entry in sys.argv[5:]:
    name, state, version = (entry.split(":", 2) + ["", ""])[:3]
    providers[name] = {"state": state, "version": version or None}
json.dump({
    "fingerprint": fp,
    "status": status,
    "pillow": pillow == "yes",
    "providers": providers,
    "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}, open(state_file, "w"), indent=2)
PY

# ---- report -----------------------------------------------------------------
if [ "$JSON" -eq 1 ]; then
  cat "$STATE_FILE" 2>/dev/null
  exit "$CODE"
fi

if [ "$QUIET" -eq 1 ] && [ "$CODE" -eq 0 ]; then
  exit 0
fi

{
  if [ "$FIRST_RUN" -eq 1 ]; then
    echo "image-gen: first run on this machine, checking the setup."
  fi
  for p in "${providers[@]}"; do
    name="${p%%:*}"; rest="${p#*:}"; state="${rest%%:*}"; version="${rest#*:}"
    case "$state" in
      ok)      printf '  ok       %-12s %s\n' "$name" "$version" ;;
      missing) printf '  --       %-12s not installed\n' "$name" ;;
      *)       printf '  WARN     %-12s %s (%s)\n' "$name" "$version" "$state" ;;
    esac
  done
  [ "$PILLOW" = "yes" ] && printf '  ok       %-12s available\n' "Pillow"

  for n in "${notes[@]:-}"; do [ -n "$n" ] && echo "  note     $n"; done

  if [ ${#problems[@]} -gt 0 ]; then
    echo
    echo "Fix before generating:"
    for p in "${problems[@]}"; do echo "  * $p"; done
  fi

  if [ "$CODE" -eq 2 ]; then
    cat <<'EOF'

Neither provider is installed. Tell the user this plainly and do NOT substitute an SVG or a
CSS drawing: that is a different deliverable and they did not ask for it.

  Codex (ChatGPT images) - preferred
    npm install -g @openai/codex
    codex            # launch once, sign in with your ChatGPT account

  Antigravity (Gemini images) - faster, more atmospheric
    Download the IDE from https://antigravity.google, install, launch, sign in
    agy install      # puts `agy` on PATH (binary at ~/.local/bin/agy)

Either one is enough. Re-run this check afterwards:
  preflight.sh --force
EOF
  elif [ "$CODE" -eq 0 ]; then
    echo
    echo "Ready. Cached, so the next run costs a few stat calls; it re-checks by itself when a"
    echo "binary or the Antigravity settings change."
  fi
} >&2

exit "$CODE"
