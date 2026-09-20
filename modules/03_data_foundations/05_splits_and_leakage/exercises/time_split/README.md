# Chronological transaction split

## Goal

Build deterministic train, validation, and test partitions without allowing future
transactions to leak into an earlier partition.

## Difficulty

Intermediate.

## Estimated time

35–50 minutes.

## Requirements

Implement `chronological_split(frame, train_fraction, validation_fraction)` in
`starter.py`. The frame has a `timestamp` column. Sort a copy by timestamp using a
stable sort, keep equal-timestamp rows in their original relative order, and return
independent train, validation, and test frames without mutating the caller's frame.

Use `floor(n * train_fraction)` rows for train and
`floor(n * validation_fraction)` rows for validation. Put every remaining row in test.
Require `0 < train_fraction < 1`, `0 <= validation_fraction < 1`, and a combined
fraction below one.

## Acceptance criteria

Partition sizes follow the floor-based rule exactly. Concatenating the three outputs
reconstructs the stable chronological order. Duplicate timestamps preserve input order,
and no timestamp in train is later than a timestamp that begins validation or test.
Invalid fractions raise `ValueError` and the input frame remains unchanged.

## Commands

Run from the repository root:

```powershell
uv run pytest modules/03_data_foundations/05_splits_and_leakage/exercises/time_split -q -rx
```

## Hints

Pandas sorting accepts a stable `kind`. Calculate both cut positions from the original
row count, then slice with `iloc` and copy each result. Think about what ordinary
rounding would do differently for seven rows.
