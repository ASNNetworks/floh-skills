#!/usr/bin/env python3
"""Render a deck JSON to a 1080x1350 LinkedIn carousel PDF.

Usage:
    python3 render.py deck.json -o carousel.pdf [--font /path/to/Inter.ttf]

Needs reportlab:
    pip install reportlab

Validation runs BEFORE any drawing, and a body over 25 words is a hard error rather than
a shrunk font: a slide nobody can read at feed size is worse than one extra slide.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

W, H = 1080, 1350          # 4:5 — the tallest ratio LinkedIn accepts
MARGIN = 88
MAX_BODY_WORDS = 25
MAX_LINE_CHARS = 32

try:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
except ImportError:
    raise SystemExit(
        "reportlab is not installed, so no PDF can be produced.\n"
        "    pip install reportlab\n"
        "Refusing to write a broken file instead."
    )

DEFAULTS = {
    "accent": "#84CC16",
    "background": "#0B1020",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "font": "Helvetica",
}


# ------------------------------------------------------------------ validation
def validate(deck: dict) -> list[str]:
    """Return hard errors. Warnings are printed separately and do not block."""
    errors: list[str] = []
    slides = deck.get("slides") or []

    if not slides:
        return ["deck has no slides"]

    kinds = [s.get("kind") for s in slides]
    if kinds[0] != "hook":
        errors.append("slide 1 must be a 'hook'")
    if kinds.count("hook") != 1:
        errors.append(f"exactly one 'hook' expected, found {kinds.count('hook')}")
    if kinds[-1] != "cta":
        errors.append("the last slide must be a 'cta'")
    if kinds.count("cta") != 1:
        errors.append(f"exactly one 'cta' expected, found {kinds.count('cta')}")

    for i, s in enumerate(slides, 1):
        if s.get("kind") == "point":
            words = len((s.get("body") or "").split())
            if words > MAX_BODY_WORDS:
                errors.append(
                    f"slide {i}: body is {words} words, over the {MAX_BODY_WORDS} cap. "
                    "Split it into two slides rather than shrinking the type."
                )
        if s.get("kind") == "list" and len(s.get("items") or []) > 5:
            errors.append(f"slide {i}: {len(s['items'])} list items, more than 5 stops being a slide")
        if s.get("kind") == "recap" and len(s.get("items") or []) != 3:
            errors.append(f"slide {i}: a recap holds exactly 3 items, found {len(s.get('items') or [])}")

    for key, val in (deck.get("theme") or {}).items():
        if key != "font" and isinstance(val, str) and not val.startswith("#"):
            errors.append(f"theme.{key} = {val!r} is not a hex colour")

    return errors


def warnings_for(deck: dict) -> list[str]:
    n = len(deck.get("slides") or [])
    if n < 8:
        return [f"{n} slides: under 8 rarely justifies the swipe"]
    if n > 12:
        return [f"{n} slides: over 12 and drop-off outruns the reach gain"]
    return []


# --------------------------------------------------------------------- drawing
class Deck:
    def __init__(self, deck: dict, font_path: str | None) -> None:
        self.slides = deck["slides"]
        self.meta = deck.get("meta") or {}
        theme = {**DEFAULTS, **(deck.get("theme") or {})}
        self.accent = HexColor(theme["accent"])
        self.bg = HexColor(theme["background"])
        self.fg = HexColor(theme["text"])
        self.muted = HexColor(theme["muted"])
        self.font, self.bold, self.mono = self._fonts(theme["font"], font_path)

    def _fonts(self, name: str, path: str | None) -> tuple[str, str, str]:
        """Register a TTF when given one; otherwise fall back and SAY so."""
        if path:
            p = Path(path)
            if not p.exists():
                raise SystemExit(f"--font {path} does not exist")
            pdfmetrics.registerFont(TTFont("deck", str(p)))
            bold = p.with_name(p.stem.replace("Regular", "Bold") + p.suffix)
            if bold.exists():
                pdfmetrics.registerFont(TTFont("deck-bold", str(bold)))
                return "deck", "deck-bold", "Courier"
            print(f"note: no bold companion for {p.name}; headlines use the regular weight")
            return "deck", "deck", "Courier"
        if name not in ("Helvetica", "Courier", "Times-Roman"):
            print(
                f"note: '{name}' is not a built-in PDF font and no --font was given. "
                "Falling back to Helvetica, which is NOT embedded. For a deck you are "
                "actually posting, pass --font with a TTF so LinkedIn's thumbnailer has "
                "the glyphs."
            )
        return "Helvetica", "Helvetica-Bold", "Courier"

    # -- primitives ---------------------------------------------------------
    def _wrap(self, c, text: str, size: int, font: str, x: int, y: int,
              width: int = W - 2 * MARGIN, leading: float = 1.25) -> int:
        chars = max(12, int(width / (size * 0.52)))
        lines = textwrap.wrap(text, width=min(chars, MAX_LINE_CHARS * 2))
        c.setFont(font, size)
        for line in lines:
            c.drawString(x, y, line)
            y -= int(size * leading)
        return y

    def _page(self, c, index: int, total: int, numbered: bool = True) -> None:
        c.setFillColor(self.bg)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(self.accent)
        c.rect(0, H - 10, W, 10, fill=1, stroke=0)
        if numbered:
            c.setFillColor(self.muted)
            c.setFont(self.font, 20)
            c.drawRightString(W - MARGIN, 52, f"{index}/{total}")
        if handle := self.meta.get("handle"):
            c.setFillColor(self.muted)
            c.setFont(self.font, 20)
            c.drawString(MARGIN, 52, handle)

    # -- slide kinds --------------------------------------------------------
    def hook(self, c, s, i, n):
        self._page(c, i, n, numbered=False)
        y = H - 300
        if kicker := s.get("kicker"):
            c.setFillColor(self.accent)
            c.setFont(self.bold, 24)
            c.drawString(MARGIN, y + 90, kicker.upper())
        c.setFillColor(self.fg)
        y = self._wrap(c, s["headline"], 72, self.bold, MARGIN, y, leading=1.18)
        if sub := s.get("sub"):
            c.setFillColor(self.muted)
            self._wrap(c, sub, 32, self.font, MARGIN, y - 40)
        c.setFillColor(self.accent)
        c.rect(MARGIN, 150, 120, 8, fill=1, stroke=0)

    def point(self, c, s, i, n):
        self._page(c, i, n)
        y = H - 380
        c.setFillColor(self.fg)
        y = self._wrap(c, s["headline"], 48, self.bold, MARGIN, y, leading=1.2)
        if body := s.get("body"):
            c.setFillColor(self.muted)
            self._wrap(c, body, 28, self.font, MARGIN, y - 44)

    def list_(self, c, s, i, n):
        self._page(c, i, n)
        y = H - 360
        c.setFillColor(self.fg)
        y = self._wrap(c, s["headline"], 48, self.bold, MARGIN, y) - 50
        for item in s.get("items", []):
            c.setFillColor(self.accent)
            c.circle(MARGIN + 8, y + 10, 8, fill=1, stroke=0)
            c.setFillColor(self.fg)
            y = self._wrap(c, item, 30, self.font, MARGIN + 40, y, width=W - 2 * MARGIN - 40) - 26

    def quote(self, c, s, i, n):
        self._page(c, i, n)
        c.setFillColor(self.accent)
        c.setFont(self.bold, 140)
        c.drawString(MARGIN, H - 300, '"')
        c.setFillColor(self.fg)
        y = self._wrap(c, s["text"], 40, self.font, MARGIN, H - 420, leading=1.35)
        if attr := s.get("attribution"):
            c.setFillColor(self.muted)
            c.setFont(self.font, 26)
            c.drawString(MARGIN, y - 40, attr)

    def code(self, c, s, i, n):
        self._page(c, i, n)
        y = H - 340
        c.setFillColor(self.fg)
        y = self._wrap(c, s.get("headline", ""), 44, self.bold, MARGIN, y) - 40
        lines = (s.get("code") or "").splitlines()[:12]
        box_h = len(lines) * 30 + 48
        c.setFillColor(HexColor("#111827"))
        c.roundRect(MARGIN, y - box_h + 20, W - 2 * MARGIN, box_h, 14, fill=1, stroke=0)
        c.setFillColor(self.accent)
        c.setFont(self.mono, 22)
        ty = y - 16
        for line in lines:
            c.drawString(MARGIN + 28, ty, line[:44])
            ty -= 30

    def recap(self, c, s, i, n):
        self.list_(c, {**s, "headline": s.get("headline", "Onthoud dit")}, i, n)

    def cta(self, c, s, i, n):
        self._page(c, i, n, numbered=False)
        y = H - 420
        c.setFillColor(self.fg)
        y = self._wrap(c, s["headline"], 56, self.bold, MARGIN, y)
        if body := s.get("body"):
            c.setFillColor(self.muted)
            y = self._wrap(c, body, 30, self.font, MARGIN, y - 40)
        c.setFillColor(self.accent)
        c.rect(MARGIN, y - 90, 300, 6, fill=1, stroke=0)
        if logo := self.meta.get("logo"):
            if Path(logo).exists():
                c.drawImage(ImageReader(logo), MARGIN, 140, width=120, height=120,
                            mask="auto", preserveAspectRatio=True)

    def render(self, out: Path) -> None:
        c = canvas.Canvas(str(out), pagesize=(W, H))
        c.setTitle(self.meta.get("title", "carousel"))
        handlers = {
            "hook": self.hook, "point": self.point, "list": self.list_,
            "quote": self.quote, "code": self.code, "recap": self.recap, "cta": self.cta,
        }
        total = len(self.slides)
        for i, s in enumerate(self.slides, 1):
            handler = handlers.get(s.get("kind"))
            if handler is None:
                raise SystemExit(f"slide {i}: unknown kind {s.get('kind')!r}")
            handler(c, s, i, total)
            c.showPage()
        c.save()


def main() -> int:
    ap = argparse.ArgumentParser(description="Render a LinkedIn carousel PDF")
    ap.add_argument("deck", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("carousel.pdf"))
    ap.add_argument("--font", default=None, help="path to a TTF to embed")
    args = ap.parse_args()

    deck = json.loads(args.deck.read_text(encoding="utf-8"))

    if errors := validate(deck):
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 1
    for w in warnings_for(deck):
        print(f"warning: {w}", file=sys.stderr)

    Deck(deck, args.font).render(args.out)
    size = args.out.stat().st_size
    print(f"{args.out}  {len(deck['slides'])} slides  {W}x{H}  {size / 1024:.0f} KB")
    print("Check it at 20% zoom before posting. If the headline is unreadable there, it is "
          "unreadable in the feed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
