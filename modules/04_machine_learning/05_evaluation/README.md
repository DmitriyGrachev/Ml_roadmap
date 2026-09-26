# Metrics and error slices

## Goal

Explain what a metric rewards and which rows the model fails on. Connect a threshold to
the cost of unnecessary watering versus missed dry plants before final test evaluation.

## Java mental model

A headline metric resembles an average endpoint latency: it can hide an unusable subgroup.
An error slice is a diagnostic view, not a separate training or tuning permission.

## Python model

Use `mean_absolute_error` for errors in the target's units and RMSE when large errors
deserve greater weight. For classification, inspect precision, recall and confusion
counts at a fixed threshold, plus a probability metric such as Brier loss. Report slice
support alongside the metric so a two-row slice is not mistaken for strong evidence.

## Key concepts

- Accuracy can hide rare positives; precision and recall answer different questions.
- Probability quality and thresholded decision quality are different properties.
- MAE and RMSE measure regression errors; classification metrics require labels or probabilities.
- Tune thresholds only on validation data; freeze them before the final test report.
- Predefine meaningful slices such as shade/sun or sensor type. Small slices are noisy;
  inspecting many slices can produce chance differences.

Reference: [metrics and scoring](https://scikit-learn.org/stable/modules/model_evaluation.html).

## Example

```powershell
uv run python modules/04_machine_learning/05_evaluation/example.py
```

Cycling-duration predictions show how a large hill error changes RMSE more than MAE,
and how overall error hides a weak route category. These regression mechanics complement
the later classification report without implementing its calculations.

## Exercises

Explain which route needs more investigation in the example, then implement the
[evaluation report](../06_reproducibility/exercises/evaluation_report/README.md) after
the reproducibility lesson. Keep the threshold explicit in every comparison.

## Self-check

1. Why can good ranking coexist with poor probability estimates?
2. What would change if a slice had three rows instead of three thousand?
3. Why must threshold choice precede final test evaluation?

## Done when

You can report an overall score, a meaningful error slice and its support, while stating
which decisions were made before the evaluation data was inspected.
