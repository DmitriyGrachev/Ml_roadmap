# Compare paired release evaluations

Difficulty: Medium. Estimated time: 45–75 minutes.

Prerequisites: LLM evaluation, keyed joins, immutable records, and lesson 02.
Compare two frozen versions of a museum assistant on the same labeled cases.
This is an offline policy check; it performs no deployment or statistical significance test.

## Contract

Implement `evaluate_release` in `starter.py`:

1. Validate policy before records. `min_cases_per_slice` is a positive integer,
   excluding booleans. `max_regression` is a finite integer/float in `[0, 1]`,
   excluding booleans. Invalid policy raises `ValueError` naming `min_cases` or `regression`.
2. Both sequences must be nonempty. Each has unique nonblank string `case_id` values,
   nonblank string slice names, and actual booleans for `passed`. Preserve valid strings
   exactly. Their case-ID sets must match, and each paired ID must have the same slice.
   Missing predictions are an invalid evaluation, never an implicit success or exclusion.
   Invalid records raise `ValueError` mentioning `case`, `slice`, `passed`, `empty`, or `ID`.
3. Join by exact case ID, irrespective of sequence order. For every observed slice,
   return its count and the baseline/candidate pass fractions as Python floats.
4. A slice below the minimum yields reason `"<slice>:insufficient-data"`. Otherwise
   it yields `"<slice>:regression"` when
   `baseline_rate - candidate_rate > max_regression + 1e-12`.
   The fixed `1e-12` allowance is solely a float comparison boundary, not a claim about
   sampling uncertainty. Equality at the allowed regression passes.
5. An insufficient slice has only the insufficient-data reason, even if its observed
   score regresses. Order `slices` and `reasons` lexicographically by exact slice name.
   Set `accepted=True` only when no reason remains. Every observed slice must pass;
   a better overall average cannot compensate for a rejected slice.
6. Return the frozen `GateReport`; do not mutate inputs or include timings/timestamps.

## Example

Baseline has two successful `facts` cases. Candidate passes one of those same cases.
The slice comparison is `SliceComparison("facts", 2, 1.0, 0.5)`. With the default
policy the report is rejected with `("facts:regression",)`; `max_regression=0.5`
accepts it. A one-case slice fails the default minimum even with a perfect score.

## TODO boundary and run

Implement `evaluate_release`, including validation, pairing, and the decision policy.
Result dataclasses are supplied; the algorithm is intentionally unsolved.

```powershell
uv run pytest modules/08_production_ai/02_releases_evaluation/exercises/release_gate -q -rx
```

Untouched work reports `xfail`. Completion means all tests pass with zero xfails and
you can explain how a missing required population could evade an observed-slices-only gate.
A real release additionally specifies which slices must exist and validates dataset provenance.
