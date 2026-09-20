# Stage 03 — Pandas analysis

## Prerequisites

Complete Stages 01–02 and the Pandas data-loading, dtypes, grouping, sorting, categoricals, and
datetime lessons. Understand that this stage explicitly converts domain `Decimal` amounts to a
floating-point analysis boundary.

## Goal

Create a stable transaction DataFrame and a deterministic UTC-day/currency summary without
mutating domain objects or caller-owned frames.

## Estimated time

60–90 minutes

## Edit

Edit only `transaction_frame` and `daily_currency_summary` in
`projects/banking_ai_lab/banking_ai_lab/dataframe.py`.

## Requirements

- Emit the nine dataset columns in canonical order from a one-shot transaction iterable.
- Use Pandas string IDs/user IDs/merchants, `float64` amounts, categorical currency/category/status,
  `datetime64[ns, UTC]` timestamps, and `bool` fraud labels for populated and empty frames.
- Keep supported currency and status category order; sort observed category values alphabetically.
- Return summary columns `day,currency,transaction_count,total_amount,fraud_count` ordered by UTC
  day and currency.
- Use UTC-aware day values, Pandas string currencies, `int64` counts, and `float64` totals in both
  populated and empty summary frames.
- Do not reorder/mutate the input transaction collection or mutate the input DataFrame.

## Acceptance criteria

Populated, empty, one-shot, dtype, value, category-order, aggregation-order, and non-mutation checks
all pass with the exact named schemas.

## Run

`uv run pytest projects/banking_ai_lab/tests/test_dataframe.py -q -rx`

## Hints (optional)

Construct explicit Series dtypes instead of relying on inference, especially for empty frames.
Normalize timestamps before deriving a day and use named aggregations so output columns remain clear.

## Completion checklist

- [ ] Empty and populated frames expose the same dtype contract.
- [ ] The iterable is consumed once and input order is unchanged.
- [ ] Daily/currency totals and fraud counts are ordered and named exactly.
- [ ] The source DataFrame is byte-for-byte equivalent by Pandas comparison after summarization.
