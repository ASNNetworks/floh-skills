# Extraction schemas

Every schema returns three things per field: the value, a confidence between 0 and 1, and
a reason. A field below 0.8 goes to a human. That is the contract, and it is the only
reason this output can be trusted downstream.

## invoice

```json
{
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD | null",
  "supplier": { "name": "string", "vat_number": "string|null", "iban": "string|null" },
  "customer": { "name": "string", "reference": "string|null" },
  "lines": [
    { "description": "string", "quantity": 0, "unit_price": 0.0, "line_total": 0.0 }
  ],
  "subtotal": 0.0,
  "vat": [{ "rate": 21, "amount": 0.0 }],
  "total": 0.0,
  "currency": "EUR",
  "is_credit_note": false
}
```

Reconciliation, always, before returning:

- `sum(lines[].line_total) == subtotal`
- `subtotal + sum(vat[].amount) == total`
- each `line_total == quantity * unit_price`

A failing check drops the confidence of every amount to at most 0.4. Do not "fix" a
number to make the sum work.

## receipt

Same shape, minus `customer`, `due_date` and `invoice_number`. Adds:

```json
{ "merchant": "string", "timestamp": "YYYY-MM-DDTHH:MM", "payment_method": "string|null" }
```

Receipts are thermal prints. Expect OCR noise in exactly two places: the amount column,
where `8` and `B` swap, and the date, where the year loses a digit. Both are caught by
reconciliation and by a sanity check that the date is not in the future.

## contract

```json
{
  "parties": [{ "name": "string", "role": "string" }],
  "effective_date": "YYYY-MM-DD",
  "term": { "months": 0, "auto_renew": true, "notice_period_days": 0 },
  "value": { "amount": 0.0, "currency": "EUR", "period": "month|year|one-off" },
  "governing_law": "string|null",
  "termination_clauses": ["string"]
}
```

Never summarise a termination clause into your own words in the structured output. Quote
it. A paraphrase of a notice period is a legal claim you are not in a position to make.

## packing_slip

```json
{
  "shipment_number": "string",
  "order_reference": "string|null",
  "ship_date": "YYYY-MM-DD",
  "lines": [{ "sku": "string", "description": "string", "quantity_ordered": 0, "quantity_shipped": 0 }]
}
```

Flag every line where `quantity_shipped != quantity_ordered`. That difference is the whole
reason anyone reads a packing slip.

## Confidence, calibrated

| Score | Means |
|-------|-------|
| 1.0 | Unambiguous. ISO date, checksummed IBAN, exact label match |
| 0.9 | Clear label, clean value, reconciles |
| 0.8 | Found by position or by a well-known layout, and consistent |
| 0.6 | Inferred from context. A human should glance at it |
| 0.3 | Present but contradicted by another field |
| 0.0 | Not found. Return null with a reason |

Do not report 0.95 because the answer feels right. If the only evidence is that the number
sits where a total usually sits, that is 0.8, and it should say so.
