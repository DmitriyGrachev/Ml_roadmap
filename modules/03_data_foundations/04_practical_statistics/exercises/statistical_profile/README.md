# Statistical amount profile

## Goal

Summarize transaction amounts with descriptive statistics while handling missing and
invalid numeric values deliberately.

## Difficulty

Intermediate.

## Estimated time

30–45 minutes.

## Requirements

Implement `describe_amounts(values)` in `starter.py`. Return the frozen
`StatisticalProfile` with `mean`, `median`, `variance`, `standard_deviation`, `p25`,
`p75`, and `p95`. Use population variance and population standard deviation. Ignore
`NaN` values when at least one finite value remains, reject positive or negative
infinity, and never mutate the input array.

## Acceptance criteria

The profile must demonstrate the different response of mean and median to an outlier.
Percentiles use NumPy's default linear interpolation. Empty and all-`NaN` arrays raise
`ValueError`, as do arrays containing infinity. The returned dataclass has exactly the
documented fields and is immutable.

## Commands

Run from the repository root:

```powershell
uv run pytest modules/03_data_foundations/04_practical_statistics/exercises/statistical_profile -q -rx
```

## Hints

Build one finite working array without changing the caller's array. NumPy provides
mean, median, variance, standard deviation, and percentile operations; check the `ddof`
convention before choosing the variance operation.
