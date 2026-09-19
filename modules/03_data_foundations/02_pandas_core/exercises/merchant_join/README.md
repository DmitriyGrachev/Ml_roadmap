# Merchant risk join

## Goal

Join merchant risk data to transactions while making a many-to-one assumption explicit.

## Difficulty

Intermediate.

## Estimated time

25–35 minutes.

## Requirements

Implement `attach_merchant_risk(transactions, merchants)` in `starter.py`. Transactions
require `transaction_id`, `merchant_id`, and `amount`; merchants require `merchant_id`
and `risk_band`. Reject duplicate merchant keys and missing required columns with
`ValueError`. Do not mutate either input.

## Acceptance criteria

Return the transaction columns followed by `risk_band`, preserving every transaction's
left-row order and the original transaction row count. Use a many-to-one merge validation
so accidental cardinality expansion cannot silently duplicate transactions.

## Commands

Run from the repository root:

```powershell
uv run pytest modules/03_data_foundations/02_pandas_core/exercises/merchant_join -q -rx
```

## Hints

Check duplicated merchant keys before the join. Read the `validate` and `sort` options
on `DataFrame.merge`, then compare the output row count to the left frame.
