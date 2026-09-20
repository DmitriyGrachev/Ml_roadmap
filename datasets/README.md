# Synthetic transaction datasets

These CSV files are deterministic learning fixtures for the Banking AI Lab. Every record and
identifier is generated; no row represents a real person, account, card, merchant relationship, or
financial event.

## Files

- `transactions.csv` contains 1,000 valid synthetic transactions generated with seed `20260919`.
- `transactions_dirty.csv` is a compact validation fixture. It deliberately contains a repeated ID,
  a byte-identical duplicate row, an invalid amount, an invalid timestamp, an unknown status, and a
  missing optional category.

The schema is ordered as `id,user_id,amount,currency,merchant,category,timestamp,status,is_fraud`.
Amounts are positive decimal strings with two places. Timestamps use aware UTC ISO 8601 values.
Supported currencies are EUR, GBP, MDL, and USD; supported statuses are approved, declined, pending,
and refunded. The `is_fraud` column uses lowercase `true` and `false`.

The fraud label is synthetic and intentionally rare. Its generated probability is modestly higher
for the synthetic `Harbor Crypto` merchant, amounts of at least 2,000, GBP/USD transactions, and
declined status. These are learning-only correlations, not claims about real customers, merchants,
currencies, or fraud behavior.

## Reproduce the files

From the repository root:

```powershell
uv run python scripts/generate_transactions.py --output datasets --seed 20260919 --count 1000
uv run pytest tests/datasets/test_transaction_generation.py -q
```

The generator uses a local seeded random source and UUID5 names derived only from the seed and row
index. The repository's existing LF policy keeps its UTF-8 CSV bytes stable on Windows, macOS, and
Linux. Do not replace these files with exported production, personal, or private financial data.
