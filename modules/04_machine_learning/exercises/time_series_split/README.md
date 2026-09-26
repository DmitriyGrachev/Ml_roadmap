# Chronological weather split with a gap

Difficulty: Medium

## Prerequisites and time

Python tuples, sorting, frozen dataclasses, and the Module 04 validation lesson. Estimated time: 45–60 minutes.

## Goal and TODO boundary

Practice splitting synthetic environmental measurements when nearby observations may
be correlated. Implement `chronological_split`; record validation and result types
are provided. No estimator, real weather feed, or external data is needed.

## Contract

- Inputs are a tuple of `Measurement(id, observed_at, value)` records. IDs are
  nonblank strings and unique; preserve exact IDs. Observation times are unique
  integers on any consistent time scale; negative times are allowed. Equal times
  are rejected so one instant cannot cross the boundary.
- Values are finite Python integers or floats. Booleans are rejected for numeric
  fields. Every input row is validated, including rows that will be skipped or unused.
- `train_size` and `test_size` are positive integers; `gap` is a nonnegative
  integer, default 0. Reject booleans and nonintegers with `ValueError`.
- Require at least `train_size + gap + test_size` rows. All invalid inputs raise
  `ValueError`; an empty collection therefore cannot supply these windows.
- Sort by ascending `observed_at`. Train on the first `train_size` rows, skip the
  next `gap` rows, and test on the next `test_size` rows. Ignore any later tail.
  The gap counts **rows**, not elapsed time.
- Return `TemporalSplit(train, test)` with tuples in time order. Do not mutate
  inputs or retain state across calls. This contract makes no random split.

## Hand-calculated example

For shuffled timestamps `[5, 1, 4, 0, 3, 2]`, with `train_size=2`,
`gap=1`, and `test_size=2`, training times are `(0, 1)` and test times
are `(3, 4)`. Time 2 is the gap; time 5 is unused.

## Optional hints

Separate validation from selection. Half-open slice boundaries make it easier to
explain exactly which rows are excluded. A row gap cannot replace a real
domain-specific leakage analysis.

## Run and completion

From the repository root:

```powershell
uv run pytest modules/04_machine_learning/exercises/time_series_split -q -rx
```

Implement only the named function in `starter.py`; keep the tests intact. The
untouched algorithm raises `NotImplementedError` and appears as expected-incomplete
(`xfail`) through `roadmap_tools.exercise_call`. Supplied validation checks pass
already. Completion requires every test to pass with **zero xfails**.
