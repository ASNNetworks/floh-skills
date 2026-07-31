#!/usr/bin/env python3
"""Mechanical voice checker.

Usage:
    python3 check_voice.py FILE [FILE ...]
    python3 check_voice.py --config VOICE.md FILE ...

Reads the rules from the nearest VOICE.md (or the given --config), then reports every
violation it can detect mechanically. Exits non-zero when anything is found, so it drops
straight into CI. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_FORBIDDEN_CHARS = ["—", "–"]  # em dash, en dash

DEFAULT_BANNED = [
    "in het huidige digitale landschap",
    "in today's fast-paced",
    "naadloos",
    "seamless",
    "revolutionair",
    "game changer",
    "ontketen",
    "unlock the power",
    "duik in",
    "dive into",
    "het is belangrijk op te merken",
    "it is important to note",
]

# Pronoun sets per `person` setting: matching any of these is the violation.
WRONG_PRONOUNS = {
    "first-person-singular": [r"\bwij\b", r"\bwe\b", r"\bons\b", r"\bonze\b", r"\bour\b"],
    "first-person-plural": [r"\bik\b", r"\bmijn\b", r"\bmij\b"],
    "none": [r"\bik\b", r"\bwij\b", r"\bwe\b", r"\bmijn\b", r"\bonze\b"],
}

FORMAL_READER = [r"\bu\b", r"\buw\b"]
INFORMAL_READER = [r"\bje\b", r"\bjij\b", r"\bjouw\b"]


def load_config(path: Path | None) -> dict:
    """Parse the small YAML-ish blocks out of a VOICE.md. Deliberately not a YAML parser:
    the format is three keys and a list, and a dependency for that is not worth it."""
    cfg = {
        "person": "first-person-singular",
        "reader": "informal",
        "forbidden_chars": list(DEFAULT_FORBIDDEN_CHARS),
        "banned": list(DEFAULT_BANNED),
    }
    if path is None or not path.exists():
        return cfg

    text = path.read_text(encoding="utf-8")
    if m := re.search(r"^\s*person:\s*([\w-]+)", text, re.M):
        cfg["person"] = m.group(1)
    if m := re.search(r"^\s*reader:\s*([\w-]+)", text, re.M):
        cfg["reader"] = m.group(1)
    if m := re.search(r"^\s*forbidden_chars:\s*\[(.*?)\]", text, re.M | re.S):
        cfg["forbidden_chars"] = re.findall(r'"([^"]+)"', m.group(1))
    if m := re.search(r"^\s*banned:\s*\n((?:\s*-\s*.*\n)+)", text, re.M):
        cfg["banned"] = [
            b.strip().strip('"').strip("'")
            for b in re.findall(r"^\s*-\s*(.+)$", m.group(1), re.M)
        ]
    return cfg


def find_config(start: Path) -> Path | None:
    for parent in [start.resolve(), *start.resolve().parents]:
        candidate = parent / "VOICE.md"
        if candidate.is_file():
            return candidate
    return None


def check(path: Path, cfg: dict) -> list[tuple[int, str, str]]:
    """Return (line_number, rule, detail) for each violation."""
    findings: list[tuple[int, str, str]] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    wrong = WRONG_PRONOUNS.get(cfg["person"], [])
    reader_wrong = FORMAL_READER if cfg["reader"] == "informal" else INFORMAL_READER

    in_fence = False
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        low = line.lower()

        for ch in cfg["forbidden_chars"]:
            if ch in line:
                findings.append((n, "forbidden-char", f"{ch!r} — use a comma, a colon, or two sentences"))

        for phrase in cfg["banned"]:
            if phrase.lower() in low:
                findings.append((n, "banned-phrase", f"{phrase!r} carries no information"))

        for pat in wrong:
            if re.search(pat, low):
                findings.append((n, "pronoun", f"{pat} does not match person={cfg['person']}"))
                break

        for pat in reader_wrong:
            if re.search(pat, low):
                findings.append((n, "reader", f"{pat} does not match reader={cfg['reader']}"))
                break

        if len(re.findall(r"!", line)) and not re.search(r"!(=|\[)", line):
            findings.append((n, "exclamation", "exclamation mark outside an interjection"))

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Mechanical brand-voice checker")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--config", type=Path, default=None, help="path to VOICE.md")
    args = ap.parse_args()

    cfg = load_config(args.config or find_config(args.files[0].parent))

    total = 0
    for path in args.files:
        if not path.is_file():
            print(f"skip  {path} (not a file)", file=sys.stderr)
            continue
        for line_no, rule, detail in check(path, cfg):
            print(f"{path}:{line_no}: {rule}: {detail}")
            total += 1

    if total:
        print(f"\n{total} violation(s).", file=sys.stderr)
        return 1
    print("Voice is clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
