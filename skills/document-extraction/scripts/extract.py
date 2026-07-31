#!/usr/bin/env python3
"""Document extraction: detect, read, parse, reconcile.

Usage:
    python3 extract.py detect  FILE
    python3 extract.py text    FILE
    python3 extract.py run     FILE [--schema invoice] [--json]

Standard library only. Text extraction shells out to `pdftotext` (poppler) and, for
scans, `tesseract` — and says so plainly when neither is installed rather than returning
empty fields, which is the failure mode this whole skill exists to prevent.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

MONTHS = {
    "jan": 1, "feb": 2, "mrt": 3, "maa": 3, "mar": 3, "apr": 4, "mei": 5, "may": 5,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11,
    "dec": 12,
}

CREDIT_MARKERS = ("creditnota", "credit note", "creditfactuur", "credit memo")


@dataclass
class Field:
    value: object = None
    confidence: float = 0.0
    reason: str = ""


@dataclass
class Result:
    kind: str = "invoice"
    is_credit_note: bool = False
    fields: dict[str, Field] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def set(self, name: str, value: object, confidence: float, reason: str = "") -> None:
        self.fields[name] = Field(value, confidence, reason)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "is_credit_note": self.is_credit_note,
            "fields": {
                k: {"value": v.value, "confidence": round(v.confidence, 2), "reason": v.reason}
                for k, v in self.fields.items()
            },
            "needs_review": [k for k, v in self.fields.items() if v.confidence < 0.8],
            "warnings": self.warnings,
        }


# --------------------------------------------------------------------------- detect
def detect(path: Path) -> str:
    """Return 'text', 'scan', 'mixed' or 'plain'."""
    if path.suffix.lower() != ".pdf":
        return "plain"
    if not shutil.which("pdftotext"):
        raise SystemExit(
            "pdftotext is not installed, so a PDF cannot be classified.\n"
            "  macOS:  brew install poppler\n"
            "  Debian: apt-get install poppler-utils"
        )
    out = subprocess.run(
        ["pdftotext", "-q", str(path), "-"], capture_output=True, text=True, check=False
    ).stdout
    chars_per_page = len(out.strip()) / max(out.count("\f") or 1, 1)
    if chars_per_page > 200:
        return "text"
    return "scan" if chars_per_page < 30 else "mixed"


# ----------------------------------------------------------------------------- text
def read_text(path: Path) -> str:
    if path.suffix.lower() != ".pdf":
        return path.read_text(encoding="utf-8", errors="replace")

    kind = detect(path)
    text = subprocess.run(
        ["pdftotext", "-q", "-layout", str(path), "-"],
        capture_output=True, text=True, check=False,
    ).stdout

    if kind == "text":
        return text

    if not shutil.which("tesseract"):
        raise SystemExit(
            f"{path.name} looks like a {kind} PDF and needs OCR, but tesseract is not "
            "installed.\n"
            "  macOS:  brew install tesseract tesseract-lang\n"
            "  Debian: apt-get install tesseract-ocr tesseract-ocr-nld\n"
            "Returning nothing rather than empty fields, on purpose."
        )
    if not shutil.which("pdftoppm"):
        raise SystemExit("tesseract is present but pdftoppm (poppler) is not.")

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["pdftoppm", "-r", "300", "-png", str(path), f"{tmp}/p"], check=True
        )
        pages = []
        for img in sorted(Path(tmp).glob("p*.png")):
            pages.append(
                subprocess.run(
                    ["tesseract", str(img), "stdout", "-l", "nld+eng"],
                    capture_output=True, text=True, check=False,
                ).stdout
            )
    return text + "\n" + "\n".join(pages)


# ---------------------------------------------------------------------------- parse
def parse_amount(raw: str) -> float | None:
    """Handle both 1.234,56 and 1,234.56 without guessing wrong."""
    s = raw.strip().replace(" ", "").replace(" ", "")
    s = re.sub(r"[^\d.,\-]", "", s)
    if not s:
        return None
    if "," in s and "." in s:
        # whichever separator comes LAST is the decimal one
        dec = "," if s.rindex(",") > s.rindex(".") else "."
        thou = "." if dec == "," else ","
        s = s.replace(thou, "").replace(dec, ".")
    elif "," in s:
        # a lone comma is decimal when it is followed by exactly two digits
        s = s.replace(",", ".") if re.search(r",\d{2}$", s) else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_date(raw: str, text: str) -> tuple[str | None, float, str]:
    """Return (iso_date, confidence, reason). Never guesses DD/MM vs MM/DD blindly."""
    raw = raw.strip()

    # 1. An explicit month name settles it outright.
    if m := re.search(r"(\d{1,2})[\s-]+([a-z]{3,})[\s-]+(\d{4})", raw, re.I):
        mon = MONTHS.get(m.group(2)[:3].lower())
        if mon:
            return f"{m.group(3)}-{mon:02d}-{int(m.group(1)):02d}", 1.0, "month name"

    # 2. ISO is unambiguous.
    if m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", raw):
        return raw, 1.0, "ISO 8601"

    # 3. Numeric. Only safe when one component is over 12.
    if m := re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})", raw):
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y += 2000 if y < 100 else 0
        if a > 12:
            return f"{y}-{b:02d}-{a:02d}", 1.0, "day > 12, so DD/MM"
        if b > 12:
            return f"{y}-{a:02d}-{b:02d}", 1.0, "second component > 12, so MM/DD"
        # ambiguous — look for a Dutch/European signal elsewhere in the document
        if re.search(r"\b(btw|kvk|iban|factuurdatum|vervaldatum)\b", text, re.I):
            return f"{y}-{b:02d}-{a:02d}", 0.75, "ambiguous; Dutch document, read as DD/MM"
        return None, 0.0, f"ambiguous date {raw!r}; both DD/MM and MM/DD are valid"

    return None, 0.0, f"unrecognised date format {raw!r}"


def parse_invoice(text: str) -> Result:
    r = Result(kind="invoice")
    low = text.lower()
    r.is_credit_note = any(m in low for m in CREDIT_MARKERS)

    # invoice number. The label alternatives are ordered longest-first: matching
    # "factuur" inside "factuurnummer" leaves the regex reading "mer" as the number.
    if m := re.search(
        r"(?:factuurnummer|factuur\s*nr\.?|invoice\s*number|invoice\s*no\.?|invoice\s*#)"
        r"[ \t]*[:#]?[ \t]*([A-Z0-9][\w\-/]{2,})",
        text, re.I,
    ):
        r.set("invoice_number", m.group(1).strip(), 0.95)
    else:
        r.set("invoice_number", None, 0.0, "no invoice-number label found")

    # invoice date
    if m := re.search(r"(?:factuurdatum|invoice\s*date|datum|date)\D{0,12}"
                      r"([0-9]{1,4}[\s/.\-][A-Za-z0-9]{1,9}[\s/.\-][0-9]{2,4})", text, re.I):
        iso, conf, why = parse_date(m.group(1), text)
        r.set("invoice_date", iso, conf, why)
    else:
        r.set("invoice_date", None, 0.0, "no date label found")

    # due date, possibly as a term
    due = r.fields.get("invoice_date")
    if m := re.search(r"(?:vervaldatum|due\s*date)\D{0,12}"
                      r"([0-9]{1,4}[\s/.\-][A-Za-z0-9]{1,9}[\s/.\-][0-9]{2,4})", text, re.I):
        iso, conf, why = parse_date(m.group(1), text)
        r.set("due_date", iso, conf, why)
    elif m := re.search(r"(?:binnen|within)\s*(\d{1,3})\s*(?:dagen|days)", text, re.I):
        days = int(m.group(1))
        if due and due.value:
            d = date.fromisoformat(str(due.value)) + timedelta(days=days)
            r.set("due_date", d.isoformat(), min(0.9, due.confidence), f"invoice_date + {days} days")
        else:
            r.set("due_date", None, 0.0,
                  f"payment term of {days} days found, but no invoice_date to compute from")
    else:
        r.set("due_date", None, 0.0, "no due date and no payment term found")

    # vat number — labelled first, bare shape only as a fallback
    if m := re.search(r"(?:btw[\w\s.\-]{0,12}|vat[\w\s.\-]{0,12})[:\s]\s*([A-Z]{2}\s?[0-9A-Z]{8,14})\b",
                      text, re.I):
        r.set("vat_number", m.group(1).replace(" ", "").upper(), 0.95, "labelled")
    elif m := re.search(r"\b([A-Z]{2}\d{9}B\d{2})\b", text):
        r.set("vat_number", m.group(1), 0.8, "shape matches a Dutch VAT number")
    else:
        r.set("vat_number", None, 0.0, "not found")

    # IBAN. Checksum every candidate rather than taking the first shape match: a VAT
    # number has the same silhouette and will otherwise be reported as a bank account.
    candidates = re.findall(r"\b([A-Z]{2}\d{2}[ ]?(?:[A-Z0-9][ ]?){10,30})\b", text)
    valid = [c.replace(" ", "") for c in candidates if iban_valid(c.replace(" ", ""))]
    if valid:
        r.set("iban", valid[0], 1.0, "checksum ok")
    elif candidates:
        r.set("iban", candidates[0].replace(" ", ""), 0.3,
              "CHECKSUM FAILS — likely an OCR error, or this is not an IBAN")
    else:
        r.set("iban", None, 0.0, "not found")

    # totals
    total = grab_amount(text, r"totaal\s*incl|total\s*due|amount\s*due|te\s*betalen|^\s*totaal\b|^\s*total\b")
    subtotal = grab_amount(text, r"subtotaal|totaal\s*excl|subtotal|net\s*amount")
    # A VAT line must NOT also be the grand-total line: "Totaal incl. btw" matches both,
    # and reading it as the VAT amount is what broke reconciliation the first time.
    vat_amt = grab_amount(text, r"\bbtw\b|\bvat\b|\btax\b", exclude=r"totaal|total|te\s*betalen")

    r.set("total", total, 0.9 if total is not None else 0.0,
          "" if total is not None else "no total label found")
    r.set("subtotal", subtotal, 0.9 if subtotal is not None else 0.0,
          "" if subtotal is not None else "no subtotal label found")
    r.set("vat_amount", vat_amt, 0.85 if vat_amt is not None else 0.0,
          "" if vat_amt is not None else "no VAT label found")

    # currency
    cur = ("EUR" if "€" in text or re.search(r"\bEUR\b", text) else
           "USD" if "$" in text or re.search(r"\bUSD\b", text) else
           "GBP" if "£" in text else None)
    r.set("currency", cur, 0.95 if cur else 0.0, "" if cur else "no unambiguous currency symbol")

    # reconciliation — the check that says whether any of the above is trustworthy
    if None not in (total, subtotal, vat_amt):
        if abs((subtotal + vat_amt) - total) < 0.02:
            r.warnings.append(f"reconciles: {subtotal:.2f} + {vat_amt:.2f} = {total:.2f}")
        else:
            r.warnings.append(
                f"DOES NOT RECONCILE: subtotal {subtotal:.2f} + vat {vat_amt:.2f} "
                f"= {subtotal + vat_amt:.2f}, but total reads {total:.2f}. "
                "The extraction is wrong, not the invoice."
            )
            for key in ("total", "subtotal", "vat_amount"):
                r.fields[key].confidence = min(r.fields[key].confidence, 0.4)
    else:
        r.warnings.append("cannot reconcile: one of total/subtotal/vat is missing")

    if r.is_credit_note:
        r.warnings.append("CREDIT NOTE: the sign of every amount flips. Do not book as a payable.")

    return r


def grab_amount(text: str, label: str, exclude: str | None = None) -> float | None:
    """Find the amount on a labelled LINE, taking the rightmost number on it.

    Line-scoped on purpose. A document-wide regex with a loose character class walks
    across whitespace-aligned columns and returns a fragment of the next field, which is
    exactly how "Totaal incl. btw  1.234,56" became 0.56 the first time round.
    """
    best: float | None = None
    for line in text.splitlines():
        if not re.search(label, line, re.I):
            continue
        if exclude and re.search(exclude, line, re.I):
            continue
        # Rightmost currency-shaped token on the line: invoices are right-aligned.
        nums = re.findall(r"-?\d{1,3}(?:[.\s]\d{3})*[.,]\d{2}|-?\d+[.,]\d{2}|-?\d+", line)
        for raw in reversed(nums):
            v = parse_amount(raw)
            # A bare percentage ("BTW 21%") is a rate, not an amount.
            if v is not None and not re.search(re.escape(raw) + r"\s*%", line):
                best = v  # keep going: the LAST labelled line wins (the summary block)
                break
    return best


def iban_valid(iban: str) -> bool:
    s = iban.upper().replace(" ", "")
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{1,30}", s):
        return False
    rearranged = s[4:] + s[:4]
    digits = "".join(str(int(c, 36)) for c in rearranged)
    return int(digits) % 97 == 1


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Document extraction")
    ap.add_argument("command", choices=["detect", "text", "run"])
    ap.add_argument("file", type=Path)
    ap.add_argument("--schema", default="invoice", choices=["invoice"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.file.exists():
        print(f"{args.file} does not exist", file=sys.stderr)
        return 2

    if args.command == "detect":
        print(detect(args.file))
        return 0

    text = read_text(args.file)
    if args.command == "text":
        print(text)
        return 0

    result = parse_invoice(text)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0

    print(f"{args.file.name} → {result.kind}")
    for name, f in result.fields.items():
        mark = "✓" if f.confidence >= 0.8 else "⚠"
        val = "null" if f.value is None else f.value
        print(f"  {mark} {name:16} {val}")
        if f.reason and f.confidence < 0.8:
            print(f"    {'':16}   {f.reason}")
    for w in result.warnings:
        print(f"  · {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
