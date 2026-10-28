# Problem framing and baselines

Начните с [разобранной теории постановки задачи](theory.md), затем запустите пример и сформулируйте собственный контракт из раздела Exercises.

## Goal

Specify the unit of prediction, available features, target, prediction time and success
metric before selecting a model. Predicting tomorrow's park visits is regression;
predicting whether a plant needs watering is binary classification.

## Java mental model

A DTO schema is not a prediction contract. A field can exist in a database while being
unavailable when the service must answer. Tomorrow's observed rainfall leaks future information.

## Python model

Keep `X` (features) and `y` (target) separate. Use `DummyRegressor` or `DummyClassifier`
to establish the performance of a predictor that ignores features. Learn the baseline
only from training targets, and evaluate it on the same held-out rows as the candidate.

## Key concepts

- Regression outputs numbers; classification outputs labels or class probabilities.
- The median constant minimizes training absolute error; the mean minimizes squared error.
- A majority classifier can have high accuracy and zero recall for the rare class.
- A feature is admissible only if it is available at prediction time and stable enough to use.
- Beating a dummy model on a tiny synthetic example proves mechanics, not real-world usefulness.

References: [dummy estimators](https://scikit-learn.org/stable/modules/model_evaluation.html#dummy-estimators)
and [evaluation metrics](https://scikit-learn.org/stable/modules/model_evaluation.html).

## Example

```powershell
uv run python modules/04_machine_learning/01_problem_framing/example.py
```

Inspect a median park-visits baseline and a majority watering baseline. The output names
the metric and its unit; an accuracy alone hides the positive-class failure.

## Exercises

Write a five-line prediction contract for a public-library queue: one row, prediction
time, target horizon, admissible features and metric. Later apply the baseline comparison
in [model comparison](../04_models/exercises/model_comparison/README.md).

## Self-check

1. Why is end-of-day visitor count forbidden in a morning forecast?
2. Why compare MAE in visits rather than an unlabeled score?
3. What does a classifier with 75% accuracy and zero recall actually do?

## Done when

You can formulate one regression and one classification problem and explain which simple
baseline must be beaten before investing in a more complex model.
