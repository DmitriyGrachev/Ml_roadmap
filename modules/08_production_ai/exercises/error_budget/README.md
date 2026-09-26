# Account for a catalog service error budget

Difficulty: Medium. Estimated time: 35–60 minutes.

Prerequisites: count aggregation, `Decimal`, integer rounding, and
[03 — Observability](../../03_observability/README.md) and
[04 — Resilience](../../04_budgets_resilience/README.md).

A library catalog team reviews a release against its availability objective. Compute the
failure allowance using complete measurement windows. The caller supplies distinct,
nonoverlapping windows for the desired reporting interval; window IDs prevent accidental
replay of the same observation, but do not themselves verify time coverage or overlap.

## Contract

Implement `summarize_error_budget(windows, target, no_data)`.

1. `target` is a finite `Decimal` in `[0, 1]`, representing the required success fraction.
   `no_data` is exactly `allow` or `block`. Other inputs use the declared types.
2. Each window ID is 1–80 characters, without leading/trailing whitespace, and unique
   across all supplied windows. Counts are integers excluding booleans and satisfy
   `0 <= failures <= requests`. `complete` must be a boolean, not an integer surrogate.
3. Validate the policy and **all** windows before aggregation. Invalid input raises
   `ValueError`, even for an incomplete window. Message wording is not prescribed.
4. Include only windows with `complete=True`. Sum their requests and failures. Count all
   complete windows, including complete windows with zero requests. Incomplete windows
   contribute nothing to any total. Do not average window percentages.
5. Allowed failures are `floor(total_requests * (1 - target))`. Use the exact numeric
   target, with no float conversion. Remaining failures equal allowed failures minus
   actual failures; retain negative values to show overspend.
6. At positive traffic, `can_release` is true exactly when failures are less than or equal
   to the allowance. With zero total requests, it is true exactly when `no_data == "allow"`.
   Both empty input and only incomplete windows are possible no-data cases.
7. Return a `BudgetSummary` in its declared field order. Preserve records and input order;
   repeated calls with equal inputs return equal summaries. No deployments are performed.

## Example

For two complete windows `(900 requests, 8 failures)` and `(100 requests, 2 failures)`
with `target=Decimal("0.99")`, return `BudgetSummary(2, 1000, 10, 10, 0, True)`.
At 99 requests and one failure, the same objective allows zero whole failures, leaving
`-1` and blocking a release.

## TODO boundary and run

Implement `summarize_error_budget`; neither validation nor accounting is supplied.

```powershell
uv run pytest modules/08_production_ai/exercises/error_budget -q -rx
```

Optional hints: validate before filtering and make the zero-denominator policy explicit.
`Decimal.as_integer_ratio()` can support exact floor arithmetic independent of the active
decimal precision.

Done when the focused tests pass with zero xfails and you can explain why a remaining budget
is a policy input, not evidence of statistical significance, full monitoring coverage, or
future reliability. The caller must define user-visible failures and the reporting interval.
