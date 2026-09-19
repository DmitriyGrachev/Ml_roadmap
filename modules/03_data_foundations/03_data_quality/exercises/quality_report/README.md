# Transaction quality report

## Goal

Measure several independent transaction-quality conditions in one immutable report.

## Difficulty

Intermediate.

## Estimated time

40–55 minutes.

## Requirements

Implement `assess_transaction_quality(frame)` in `starter.py`. Required columns are
`id`, `amount`, and `timestamp`; `category` is optional. Known categories are `food`,
`travel`, and `utilities`. Do not mutate the input. Return the frozen `QualityReport`
with `missing_id_count`, `duplicate_id_count`, `invalid_amount_count`,
`invalid_timestamp_count`, and `unknown_category_count` fields.

## Acceptance criteria

Count null or blank IDs as missing. Count only repeated, present IDs after their first
occurrence as duplicates. An amount is invalid when it is missing, unparseable,
non-finite, or not positive. A timestamp is invalid when it is missing, unparseable, or
timezone-naive. Count only present optional categories outside the known set as unknown;
an absent or all-missing category column contributes zero unknown categories.

## Commands

Run from the repository root:

```powershell
uv run pytest modules/03_data_foundations/03_data_quality/exercises/quality_report -q -rx
```

## Hints

Use masks, `duplicated`, `to_numeric`, `to_datetime`, and explicit timezone checks. Work
from test rows one condition at a time so overlapping defects are counted independently.
