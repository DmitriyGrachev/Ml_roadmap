# Explicit-label wildlife classification report

Difficulty: Medium

## Prerequisites and time

Python sequences, nested counts, basic precision/recall, and the Module 04 evaluation lesson. Estimated time: 60–75 minutes.

## Goal and TODO boundary

Implement `multiclass_report` for synthetic owl, fox, and deer observations.
Validation and frozen result types are supplied; counting and all metric
calculations are TODOs. Use Python arithmetic; no model training is required.

## Contract

- `actual` and `predicted` are equally sized tuples of label strings.
  `labels` is a nonempty tuple of unique, nonblank strings defining the entire
  class space and its order. Preserve exact strings, including outer spaces.
- Every actual and predicted label must occur in `labels`. Invalid label
  definitions, unknown labels, or unequal lengths raise `ValueError`.
- The square `confusion` tuple contains actual labels on rows and predicted
  labels on columns, both in the supplied order. Include absent classes.
- Produce one `ClassMetrics(label, support, precision, recall, f1)` per label,
  in that order. Support is its actual count; precision is TP / predicted count;
  recall is TP / support; F1 is `2 * precision * recall / (precision + recall)`.
  Every zero denominator produces 0.0.
- Accuracy is diagonal total / observation count. Macro F1 is the unweighted mean
  over **all supplied labels**, including absent ones. Empty observations produce
  a full zero matrix, zero class metrics, zero accuracy and zero macro F1.
- Return `MulticlassReport(confusion, classes, accuracy, macro_f1)` without
  rounding, changing inputs, or retaining state.

## Hand-calculated example

With labels `("owl", "fox", "deer")`, actual
`("owl", "owl", "fox", "fox", "deer")` and predicted
`("owl", "fox", "fox", "deer", "deer")`, the matrix is
`((1, 1, 0), (0, 1, 1), (0, 0, 1))`. Class F1 scores are
`(2/3, 1/2, 2/3)`, accuracy is `3/5`, and macro F1 is `11/18`.

## Optional hints

Write the row/column meaning on paper first. Row totals and column totals have
different roles. Compare macro averaging with weighting by support.

## Run and completion

From the repository root:

```powershell
uv run pytest modules/04_machine_learning/exercises/multiclass_report -q -rx
```

Implement only the named function in `starter.py`; keep the tests intact. The
untouched algorithm raises `NotImplementedError` and appears as expected-incomplete
(`xfail`) through `roadmap_tools.exercise_call`. Supplied validation checks pass
already. Completion requires every test to pass with **zero xfails**.
