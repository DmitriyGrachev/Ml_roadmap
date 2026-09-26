# Summarize paired observations

Difficulty: Medium · Estimated time: 40–60 minutes

## Prerequisites

Module 03 descriptive statistics and data-quality lessons. Know means, sample
covariance, Pearson correlation, finite values, and why correlation is not causation.

## Requirements

Implement `summarize_pairs(xs, ys)` in `starter.py`. Inputs are aligned numeric
measurement sequences from two instruments, each element representable as a float.

- Reject unequal sequence lengths with `ValueError` before processing pairs; include `length` in the message.
- Retain a pair only when both values are finite. Drop the whole pair if either
  side is NaN, positive infinity, or negative infinity. Never clean the two
  sequences independently and then zip them.
- Return the provided immutable `PairSummary` with retained `count`, `mean_x`,
  `mean_y`, sample `covariance`, and Pearson `correlation`.
- With zero pairs, all four statistics are `None`. With one pair, return its
  means, but covariance and correlation are `None`.
- For two or more pairs, covariance is
  `sum((x-mean_x)*(y-mean_y)) / (count-1)` (sample, not population).
  Correlation uses the corresponding centered sums and lies in `[-1, 1]`.
- If either retained axis is constant, covariance is `0.0` and correlation is
  `None`. Do not substitute zero for undefined correlation or return NaNs.
- Do not mutate inputs. Ordinary floating-point tolerances are accepted; inputs
  are modest in magnitude, so numerical overflow engineering is outside scope.

## Example

```python
summarize_pairs([1.0, float("nan"), 5.0], [2.0, 99.0, 10.0])
# PairSummary(count=2, mean_x=3.0, mean_y=6.0, covariance=16.0, correlation=1.0)
summarize_pairs([4.0], [7.0])
# PairSummary(count=1, mean_x=4.0, mean_y=7.0, covariance=None, correlation=None)
```

## Edge cases and optional hints

Try no retained pairs, a constant axis, perfect negative correlation, and missing
values at different positions. One joint finite mask preserves alignment. Compute
centered values once, then reason about the denominators before dividing.

## Run and done when

From the repository root:

```powershell
uv run pytest modules/03_data_foundations/exercises/paired_observations -q -rx
```

Edit only `starter.py`. Done when all tests pass with zero xfails and you can
explain the sample denominator and undefined-statistic cases without relying on warnings.
