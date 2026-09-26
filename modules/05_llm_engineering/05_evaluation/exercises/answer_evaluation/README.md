# Library answer evaluation

Difficulty: **Medium**. Theme: scoring answers to library reference questions.

## Goal

Implement `evaluate_answers` to align frozen cases and predictions, validate complete
coverage, and report quality alongside latency and cost.

## Java mental model

This is a keyed join followed by aggregate metrics. Never zip positional lists or discard
unmatched records: the evaluation denominator is part of the contract.

## Python model

`Case`, `Prediction`, and `Evaluation` are provided frozen dataclasses. `None` means an
explicit refusal. Costs arrive as `Decimal` values in a common caller-defined currency;
latencies are measured milliseconds. There is no provider call or model-based grading.

## Key concepts

Require at least one case, nonblank exact-unique identifiers in each tuple, and identical
case/prediction ID sets. Raise `ValueError` mentioning `case`, `prediction`, `identifier`,
or `ID` if those constraints fail. Preserve inputs and join by exact ID, regardless of order.

Any non-`None` expected or predicted answer must be nonblank after stripping; otherwise
raise `ValueError` mentioning `answer`. A text answer matches only when both strings are
equal after `strip().casefold()`. Do not normalize internal whitespace or invent synonyms.
If the expected answer is `None`, only a prediction of `None` is correct. Refusing an
answerable case is incorrect; answering a refusal-required case is incorrect.

Require finite, nonnegative latency and finite, nonnegative decimal cost for **every**
prediction. Invalid values raise `ValueError` mentioning `latency` or `cost`. Failed-quality
predictions still consume latency and cost and must remain in those aggregates.

Return total cases, correct cases, overall accuracy, answerable-slice accuracy,
refusal-required-slice accuracy, mean latency, nearest-rank p95 latency, and total decimal
cost. A missing slice has accuracy `None`, not zero. For p95 sort all `n` latencies and
take the item at one-based rank `ceil(0.95 * n)`; do not interpolate. Do not round metrics
or convert costs through floats.

## Example

For four cases with two correct answers, overall accuracy is 0.5. Latencies 10, 20, 30,
100 ms have mean 40 ms and nearest-rank p95 100 ms. With 20 latencies 1 through 20 ms,
p95 is 19 ms, demonstrating why p95 is not always the maximum.

## Exercises

Implement the boundary and run:

```powershell
uv run pytest modules/05_llm_engineering/05_evaluation/exercises/answer_evaluation
```

The tests cover reordered predictions, duplicates, missing IDs, absent slices, explicit
refusals, Unicode case-folding, nonfinite values, percentile policy, and decimal totals.

## Self-check

1. Why is this match policy useful for narrow facts but weak for essays?
2. Why does omitting a failed prediction bias both quality and cost estimates?

## Done when

All tests pass with zero xfails. You can explain why a correct scorer is only a prerequisite
for a meaningful, representative, held-out evaluation of a live model.
