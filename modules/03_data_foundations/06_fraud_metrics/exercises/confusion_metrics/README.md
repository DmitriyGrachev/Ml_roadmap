# Fraud confusion metrics

## Goal

Calculate fraud-classification counts and metrics without letting headline accuracy
hide missed fraud.

## Difficulty

Intermediate.

## Estimated time

40–55 minutes.

## Requirements

Implement `confusion_counts(labels, predictions)`, `accuracy(counts)`,
`precision(counts)`, `recall(counts)`, and `f1(counts)` in `starter.py`. Fraud label `1`
is the positive class and label `0` is the negative class. Reject length mismatch and
non-binary values. Return the frozen `ConfusionCounts(tp, fp, tn, fn)` record.

Each metric accepts a keyword-only `zero_division` value, defaulting to `0.0`. Return
that value when the metric's denominator is zero instead of raising or returning
`NaN`.

## Acceptance criteria

Counts identify all four outcomes. Perfect predictions give each metric a value of one.
For 1 fraudulent transaction among 1,000 transactions, a predictor that always returns
`0` has accuracy `0.999` and fraud recall `0.0`. Every zero-denominator branch honors
both the default and a caller-supplied `zero_division` value. When true positives are
zero but false positives and false negatives exist, F1 is defined as `0.0`; the
`zero_division` fallback does not apply because the F1 denominator is nonzero.

## Reasoning prompt

In your own words, explain why `99.9%` accuracy is useless for the all-negative fraud
predictor. Name the operational failure that recall exposes and identify one business
cost associated with that failure. Do not change the tests to store your answer.

## Commands

Run from the repository root:

```powershell
uv run pytest modules/03_data_foundations/06_fraud_metrics/exercises/confusion_metrics -q -rx
```

## Hints

Write the four Boolean conditions explicitly before counting them. For each derived
metric, name its denominator first and handle zero before dividing.
