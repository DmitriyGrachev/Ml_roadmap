# Payment matrix conversion

## Goal

Convert a matrix of payment amounts into reporting values with NumPy broadcasting.

## Difficulty

Intermediate.

## Estimated time

20–30 minutes.

## Requirements

Implement `convert_amount_matrix(amounts, rates)` in `starter.py`. `amounts` is a
two-dimensional `float64` array shaped `(record_count, currency_count)`; `rates` is a
one-dimensional `float64` array with one value per currency. An empty row dimension is
valid. Reject nonmatching or invalid dimensions with `ValueError`, do not mutate either
input, and do not use explicit Python loops.

## Acceptance criteria

Return a `float64` array with the same shape as `amounts`, with every column converted
by its matching rate. Inputs are unchanged and incompatible shapes raise `ValueError`.

## Commands

Run from the repository root:

```powershell
uv run pytest modules/03_data_foundations/01_numpy/exercises/payment_matrix -q -rx
```

## Hints

Inspect `shape`, identify the currency `axis`, consider how a one-dimensional rate
array aligns with that final axis, and let broadcasting perform the column-wise
operation.
