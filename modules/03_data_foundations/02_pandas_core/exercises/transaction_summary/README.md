# Transaction summary

## Goal

Create a deterministic grouped summary without mutating the source transaction frame.

## Difficulty

Intermediate.

## Estimated time

35–45 minutes.

## Requirements

Implement `summarize_transactions(frame)` in `starter.py`. The required columns are
`currency`, `status`, `amount`, and timestamp-compatible `timestamp`. Parse timestamps
before summarizing. Exclude rows with a missing currency, status, amount, or timestamp;
do not modify the input frame. Treat categorical grouping values as observed groups only.

## Acceptance criteria

Return one row per observed `(currency, status)` pair, sorted ascending by both fields.
The exact output columns are `currency`, `status`, `transaction_count`, `total_amount`,
`median_amount`, and `p95_amount`. Their dtypes are respectively `string`, `string`,
`int64`, `float64`, `float64`, and `float64`. `p95_amount` is the 95th percentile of
the group's amounts.

## Commands

Run from the repository root:

```powershell
uv run pytest modules/03_data_foundations/02_pandas_core/exercises/transaction_summary -q -rx
```

## Hints

Work on a copy, use `to_datetime`, drop rows according to the documented policy, and
look at named aggregation with `groupby`. Check how categoricals can be limited to only
observed combinations.
