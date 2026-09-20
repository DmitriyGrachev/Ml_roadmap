# Fraud ranking metrics

## Goal

Measure how fraud scores rank positive examples with ROC-AUC and a documented
trapezoidal PR-AUC.

## Difficulty

Advanced.

## Estimated time

60–80 minutes.

## Requirements

Implement `roc_auc(labels, scores)` and `pr_auc(labels, scores)` in `starter.py` without
scikit-learn. Inputs must be non-empty and equal length. Labels contain only `0` and
`1`; scores must be finite probabilities in `[0, 1]`; both label classes must be
present. Raise `ValueError` when any rule is violated.

For ROC-AUC, tied positive and negative scores receive half credit, equivalently the
average-rank treatment. For PR-AUC, begin at recall `0` and precision `1`, sort
thresholds from highest score to lowest, consume every equal-score group before adding
one precision-recall point, and integrate precision over recall with the trapezoidal
rule. Reordering paired labels and scores must not change either result.

## Acceptance criteria

Both metrics match the known numeric examples within explicit floating-point tolerance.
Tied scores are grouped rather than resolved by input order. Empty data, mismatched
lengths, non-binary labels, invalid scores, and single-class labels raise clear
`ValueError` exceptions.

## Reasoning prompt

Write a short answer explaining when PR-AUC is more informative than ROC-AUC for fraud
detection. Relate the answer to rare positives, false positives, and precision; also
explain why neither ranking metric chooses an operating threshold for the business.
Do not change the tests to store your answer.

## Commands

Run from the repository root:

```powershell
uv run pytest modules/03_data_foundations/06_fraud_metrics/exercises/ranking_metrics -q -rx
```

## Hints

Validate once per function before doing numeric work. For ROC-AUC, reason about every
positive-negative score pair or equivalent ranks. For PR-AUC, inspect score groups and
record a point only after a complete group has been included.
