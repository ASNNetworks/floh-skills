#!/usr/bin/env python3
"""Technical + on-page SEO checker.

Usage:
    python3 audit.py <url-or-path> [--json]

Reads a URL or a local HTML file, and reports findings grouped by impact.
Standard library only, apart from an optional BeautifulSoup fast path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen

CRITICAL, IMPORTANT, POLISH = "critical", "important", "polish"


class Doc(HTMLParser):
    """Minimal DOM facts, gathered in one pass. No dependency on a parser library."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self.headings: list[tuple[int, str]] = []
        self.meta: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.anchors: list[tuple[str, str]] = []
        self.jsonld: list[str] = []
        self.lang: str | None = None
        self._capture: str | None = None
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._capture, self._buf = "title", []
        elif tag == "meta":
            self.meta.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag == "img":
            self.images.append(a)
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._capture, self._buf = tag, []
        elif tag == "a":
            self._capture, self._buf = "a", []
            self._href = a.get("href", "")
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._capture, self._buf = "jsonld", []

    def handle_endtag(self, tag: str) -> None:
        if self._capture is None:
            return
        text = "".join(self._buf).strip()
        if tag == "title" and self._capture == "title":
            self.title = text
        elif tag == self._capture and re.fullmatch(r"h[1-6]", tag):
            self.headings.append((int(tag[1]), text))
        elif tag == "a" and self._capture == "a":
            self.anchors.append((getattr(self, "_href", ""), text))
        elif tag == "script" and self._capture == "jsonld":
            self.jsonld.append(text)
        else:
            return
        self._capture, self._buf = None, []

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._buf.append(data)

    def meta_by_name(self, name: str) -> str | None:
        for m in self.meta:
            if m.get("name", "").lower() == name.lower():
                return m.get("content", "")
        return None

    def meta_by_property(self, prop: str) -> str | None:
        for m in self.meta:
            if m.get("property", "").lower() == prop.lower():
                return m.get("content", "")
        return None

    def link_rel(self, rel: str) -> str | None:
        for link in self.links:
            if rel in link.get("rel", "").lower().split():
                return link.get("href", "")
        return None


VAGUE_ANCHORS = {
    "hier", "klik hier", "lees meer", "meer", "link", "deze pagina",
    "here", "click here", "read more", "more", "this page", "learn more",
}


def load(target: str) -> tuple[str, dict[str, str], str | None]:
    """Return (html, headers, final_url). A local path yields empty headers."""
    if re.match(r"^https?://", target):
        req = Request(target, headers={"User-Agent": "floh-seo-audit/1.0"})
        with urlopen(req, timeout=20) as resp:  # noqa: S310 — explicit http(s) only
            body = resp.read().decode(resp.headers.get_content_charset() or "utf-8", "replace")
            return body, {k.lower(): v for k, v in resp.headers.items()}, resp.geturl()
    with open(target, encoding="utf-8") as fh:
        return fh.read(), {}, None


def audit(html: str, headers: dict[str, str], url: str | None) -> list[dict[str, str]]:
    doc = Doc()
    doc.feed(html)
    out: list[dict[str, str]] = []

    def add(level: str, check: str, detail: str) -> None:
        out.append({"level": level, "check": check, "detail": detail})

    # -- indexability -------------------------------------------------------
    robots = (doc.meta_by_name("robots") or "").lower()
    if "noindex" in robots:
        add(CRITICAL, "noindex", "meta robots contains noindex; the page cannot be indexed")
    if "noindex" in headers.get("x-robots-tag", "").lower():
        add(CRITICAL, "noindex", "X-Robots-Tag header contains noindex")

    # -- title --------------------------------------------------------------
    if not doc.title:
        add(CRITICAL, "title", "no <title>; the URL is rendered as the result title")
    else:
        n = len(doc.title)
        if n < 30:
            add(IMPORTANT, "title", f"title is {n} chars; under 30 wastes result-page space")
        elif n > 60:
            add(IMPORTANT, "title", f"title is {n} chars; over 60 is truncated in results")

    # -- headings -----------------------------------------------------------
    h1s = [t for lvl, t in doc.headings if lvl == 1]
    if not h1s:
        add(CRITICAL, "h1", "no <h1> on the page")
    elif len(h1s) > 1:
        add(CRITICAL, "h1", f"{len(h1s)} <h1> elements: {h1s!r}")
    levels = [lvl for lvl, _ in doc.headings]
    for prev, cur in zip(levels, levels[1:]):
        if cur - prev > 1:
            add(IMPORTANT, "heading-order", f"heading level jumps h{prev} to h{cur}")
            break

    # -- description --------------------------------------------------------
    desc = doc.meta_by_name("description")
    if not desc:
        add(IMPORTANT, "description", "no meta description; the snippet is auto-generated")
    else:
        n = len(desc)
        if n < 120 or n > 160:
            add(IMPORTANT, "description", f"description is {n} chars; aim for 120-160")

    # -- canonical ----------------------------------------------------------
    canonical = doc.link_rel("canonical")
    if not canonical:
        add(IMPORTANT, "canonical", "no rel=canonical")
    elif url:
        want, got = urlparse(url), urlparse(canonical)
        if got.netloc and got.netloc != want.netloc:
            add(CRITICAL, "canonical", f"canonical points to another host: {canonical}")

    # -- structured data ----------------------------------------------------
    if not doc.jsonld:
        add(IMPORTANT, "structured-data", "no JSON-LD; no rich result is possible")
    for raw in doc.jsonld:
        try:
            json.loads(raw)
        except json.JSONDecodeError as exc:
            add(CRITICAL, "structured-data", f"JSON-LD does not parse: {exc}")

    # -- social -------------------------------------------------------------
    for prop in ("og:title", "og:description", "og:image"):
        if not doc.meta_by_property(prop):
            add(IMPORTANT, "open-graph", f"missing {prop}; shares render bare")

    # -- images and links ---------------------------------------------------
    missing_alt = [i.get("src", "?") for i in doc.images if "alt" not in i]
    if missing_alt:
        add(IMPORTANT, "img-alt", f"{len(missing_alt)} image(s) without alt: {missing_alt[:10]}")
    vague = [href for href, text in doc.anchors if text.strip().lower() in VAGUE_ANCHORS]
    if vague:
        add(IMPORTANT, "anchor-text", f"{len(vague)} link(s) with non-descriptive text: {vague[:10]}")

    # -- polish -------------------------------------------------------------
    if not doc.lang:
        add(POLISH, "lang", "<html> has no lang attribute")

    order = {CRITICAL: 0, IMPORTANT: 1, POLISH: 2}
    return sorted(out, key=lambda f: order[f["level"]])


def main() -> int:
    ap = argparse.ArgumentParser(description="Technical + on-page SEO checker")
    ap.add_argument("target", help="URL or path to an HTML file")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    html, headers, url = load(args.target)
    findings = audit(html, headers, url)

    if args.json:
        print(json.dumps({"target": args.target, "findings": findings}, indent=2))
    elif not findings:
        print("No findings. The page is technically sound.")
    else:
        for f in findings:
            print(f"{f['level'].upper():9} {f['check']:18} {f['detail']}")

    return 1 if any(f["level"] == CRITICAL for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
