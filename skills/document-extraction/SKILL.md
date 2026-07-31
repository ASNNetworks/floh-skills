---
name: document-extraction
description: Pull structured data out of invoices, receipts, contracts and forms — PDF or scan — into a validated schema, with a confidence flag per field. Use when asked to read a document, extract invoice or receipt fields, digitise a stack of PDFs, or turn documents into rows.
---

# Document extraction

Turning a document into a row is easy. Turning it into a row you can *post to a ledger
without a human looking* is the hard part, and it is entirely about knowing which fields
you are unsure of.

## When to use this

Reading invoices, receipts, purchase orders, contracts, packing slips or forms into
structured data. Single file or a directory.

## How to run it

1. **Get text out of the file first.** Decide which kind of document you have:

   ```bash
   python3 scripts/extract.py detect invoice.pdf
   ```

   It reports `text` (a digital PDF with a real text layer), `scan` (images only, needs
   OCR), or `mixed`.

2. **Extract.**

   ```bash
   python3 scripts/extract.py run invoice.pdf --schema invoice --json
   ```

   For a scan, the script shells out to `pdftotext`/`tesseract` when they are installed
   and tells you plainly when they are not. Do not silently return empty fields.

3. **Read the confidence block before the data block.** Anything below the threshold is
   a field a human must confirm. Say so in your answer, by name.

4. **Never invent a missing field.** A null with a reason beats a plausible guess, every
   time. This is the rule the whole skill exists for.

## The schema

`references/schemas.md` holds the field sets. The invoice one, which covers most work:

| Field | Type | Notes |
|-------|------|-------|
| `invoice_number` | string | As printed. Do not normalise away prefixes |
| `invoice_date` | ISO date | Watch DD/MM vs MM/DD — see below |
| `due_date` | ISO date, null | Often expressed as "30 dagen" and must be computed |
| `supplier.name` | string | The party being paid |
| `supplier.vat_number` | string, null | Validate the country prefix and length |
| `supplier.iban` | string, null | Checksum it |
| `customer.name` | string | |
| `lines[]` | array | description, quantity, unit_price, line_total |
| `subtotal` | decimal | |
| `vat[]` | array | rate + amount per rate. Multiple rates are normal |
| `total` | decimal | |
| `currency` | ISO 4217 | Infer from the symbol only when it is unambiguous |

## The four mistakes that cost real money

**1. Date order.** `03/04/2026` is 3 April in the Netherlands and 4 March in the US. Do
not guess from the number alone. Resolve it from: an explicit month name elsewhere in the
document, the supplier's country, or another date in the same document where the day
exceeds 12. If none of those settle it, return the raw string and flag it. A silently
wrong invoice date lands the payment in the wrong quarter.

**2. Totals that do not reconcile.** Always check `sum(lines) == subtotal` and
`subtotal + sum(vat) == total`. When it does not add up, the extraction is wrong, not the
invoice. Report the discrepancy rather than the numbers.

**3. Credit notes read as invoices.** A negative total, or the words "creditnota" /
"credit note", flips the sign of the whole document. Booking one as a payable is a real
error with a real cost.

**4. Multi-page documents where the total is on page 3.** Do not extract page 1 and stop.
Concatenate first, extract second.

## Reporting

```
invoice.pdf → invoice
  ✓ invoice_number  2026-0417
  ✓ total           1.234,56 EUR
  ✓ reconciles      lines 1.020,30 + btw 214,26 = 1.234,56
  ⚠ due_date        null — "betaling binnen 30 dagen" found, but no invoice_date
                    to compute from. Needs a human.
```

## Files

- `scripts/extract.py` — detection, text extraction, field parsing, reconciliation.
- `references/schemas.md` — the field sets for invoice, receipt, contract and packing slip.
