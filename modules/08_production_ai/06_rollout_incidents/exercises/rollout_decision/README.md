# Decide a bounded canary rollout

Difficulty: Medium. Estimated time: 45–75 minutes.

Prerequisites: state transitions, rates, descriptive statistics, and lesson 06.
Turn ordered, completed canary measurement windows into one recommendation. This offline
function never changes traffic or performs a rollback. The caller provides nonoverlapping,
chronological windows; their sampling and representativeness are outside this exercise.

## Contract

Implement `decide_rollout(windows, policy)` in `starter.py`:

1. Validate the policy and **all** windows before making any decision, even windows
   following a would-be terminal result. Invalid input raises `ValueError` mentioning
   its field or `policy`/`window`.
2. Policy `min_requests`, `promote_after`, and `rollback_after` are positive integers,
   excluding booleans. `max_error_rate` is finite in `[0, 1]`; `max_p95_ms` is finite
   and positive. Numeric policy thresholds accept integers/floats, excluding booleans.
3. Window counts are integers, excluding booleans, with `0 <= failures <= requests`.
   At zero requests, p95 must be `None`. At positive requests, p95 must be a finite
   nonnegative integer/float, excluding booleans. There is no missing-value imputation.
4. Start with zero healthy/unhealthy streaks and scan windows in supplied order.
   A window below `min_requests` resets both streaks; its hold reason is `insufficient-data`.
5. For sufficient samples, a window is healthy exactly when both
   `failures / requests <= max_error_rate` and `p95_ms <= max_p95_ms`.
   Equality is healthy. Healthy windows increment the healthy streak and reset unhealthy;
   unhealthy windows do the reverse. This consecutive-window policy provides hysteresis.
6. At the first healthy streak reaching `promote_after`, return action `promote` and
   reason `healthy-streak`. At the first unhealthy streak reaching `rollback_after`,
   return action `rollback` and reason `unhealthy-streak`. Include windows processed
   through that decision and the current streaks; later valid windows cannot overturn it.
7. Without a terminal decision, return action `hold` and count all windows. Reason is
   `warming-up` after a healthy final window, `watching-regression` after an unhealthy
   final window, or `insufficient-data` after an undersampled final window.
   Empty input returns `RolloutDecision("hold", 0, 0, 0, "no-data")`.
8. Preserve input order and records, do not combine per-window percentiles, and make
   repeated calls deterministic. This state is recomputed from the supplied history.

## Example

With the default policy, three consecutive `Window(100, 1, 500.0)` values produce
`RolloutDecision("promote", 3, 3, 0, "healthy-streak")`. A zero-request window between
the second and third good windows resets progress; it is not a successful window.

## TODO boundary and run

Implement `decide_rollout`, including validation and the state transition policy.
Dataclasses are provided; no rollout decision algorithm is included.

```powershell
uv run pytest modules/08_production_ai/06_rollout_incidents/exercises/rollout_decision -q -rx
```

Completion means zero xfails and an explanation of why thresholds/streaks do not prove
statistical significance, account for all user slices, or replace a tested rollback plan.
