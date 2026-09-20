# Stage 01 — CSV validation

## Prerequisites

Complete the repository [setup guide](../../../../docs/setup.md), then review Python collections,
typing, data modeling, and exceptions/I/O. Be comfortable with `csv.DictReader`, Pydantic
validation errors, immutable records, `Decimal`, UUIDs, and aware datetimes.

## Goal

Import the synthetic transaction CSV while preserving valid row order and collecting safe,
field-specific issues instead of aborting on the first malformed row.

## Estimated time

60–90 minutes

## Edit

Edit only `import_transactions` in
`projects/banking_ai_lab/banking_ai_lab/importer.py`.

## Requirements

- Treat the first CSV data row as row 1 and header issues as row 0.
- Require all nine canonical headers; report missing headers in canonical column order.
- Accept lowercase `true` and `false` fraud labels and an empty optional category without silently
  normalizing other invalid values.
- Keep valid transactions in file order while collecting every independent row issue in CSV column
  order.
- Classify a later byte-identical record as a duplicate row and a reused ID with changed data as a
  duplicate transaction ID.
- Keep issue messages field-specific: never include a complete row or unrelated user/merchant data.

## Acceptance criteria

Clean and generated datasets import into frozen `Transaction` objects. Empty files, missing
headers, malformed fields, excess amount precision, exact duplicate rows, and reused IDs produce
the documented ordered issues. A missing path raises `FileNotFoundError`.

## Run

`uv run pytest projects/banking_ai_lab/tests/test_importer.py -q -rx`

## Hints (optional)

Inspect Pydantic error locations rather than copying its complete input into an issue. Track row
identity separately from transaction-ID identity, and keep the canonical columns nearby when
ordering errors.

## Completion checklist

- [ ] The valid, empty, malformed, and duplicate cases pass.
- [ ] Excess decimal precision is rejected rather than rounded.
- [ ] No issue message exposes a complete input row.
- [ ] The starter `NotImplementedError` has been replaced only in the named function.
