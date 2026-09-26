# Weather-alert threshold policy

Difficulty: Medium

## Prerequisites and time

Python loops and sorting, binary precision/recall, and the Module 04 evaluation lesson. Estimated time: 45–60 minutes.

## Goal and TODO boundary

Implement `choose_threshold` to choose a weather-alert decision rule from
supplied validation scores. Validation and `ThresholdChoice` are provided.
This is a deterministic policy exercise, not evidence that a weather model is safe.

## Contract

- `scores` and `actual` have equal length. Labels are exact integers 0 or 1
  (reject booleans). Scores, candidate thresholds, `min_recall`, and
  `min_precision` are finite Python numbers in [0, 1], excluding booleans.
  Violations raise `ValueError`, even with no candidates or observations.
- Evaluate only the supplied `thresholds`. Repeated candidates are allowed.
  Predict an alert when `score >= threshold`, including equality.
- Precision is true alerts / all alerts; recall is true alerts / all actual
  positives. A zero denominator yields 0.0. Do not round metrics.
- Keep candidates meeting both minimums inclusively. Rank feasible candidates by
  highest precision, then highest recall, then fewest alerts, then highest
  threshold. Candidate input order cannot break ties.
- Return `ThresholdChoice(threshold, precision, recall, alerts)` for the
  winner, or `None` if none qualify. Empty candidates return `None`.
  Empty observations give every candidate zero precision, recall and alerts.
- Do not mutate inputs. Select thresholds on validation data; this exercise does
  not authorize using the final test set for tuning.

## Hand-calculated example

Scores `(.9, .8, .7, .6)` with labels `(1, 0, 1, 0)` give threshold .9
precision 1 and recall .5. Threshold .7 gives precision 2/3 and recall 1.
Minimum recall .5 and precision .5 select .9; minimum recall 1 and precision .6
select .7.

## Optional hints

Count actual positives once. A tuple of tie-breaking values can express the
ranking, but check the direction of the alert-count preference.

## Run and completion

From the repository root:

```powershell
uv run pytest modules/04_machine_learning/exercises/threshold_policy -q -rx
```

Implement only the named function in `starter.py`; keep the tests intact. The
untouched algorithm raises `NotImplementedError` and appears as expected-incomplete
(`xfail`) through `roadmap_tools.exercise_call`. Supplied validation checks pass
already. Completion requires every test to pass with **zero xfails**.
