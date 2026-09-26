# Linear models, trees and validation-based selection

## Goal

Compare a simple baseline with models of increasing flexibility using the same folds
and the same metric. Select hyperparameters without consulting the reserved test set.

## Java mental model

Models are interchangeable implementations of `fit`/`predict`, but their assumptions
are not interchangeable. A more elaborate implementation does not automatically improve
the service's behavior on unseen requests.

## Python model

Ridge regression regularizes linear coefficients and benefits from comparable feature
scales. Logistic regression is a classifier despite its name. Trees learn thresholds
and interactions without scaling, but an unrestricted tree can memorize training rows.
`cross_validate` exposes per-fold scores; `GridSearchCV` selects a parameter setting.

## Key concepts

- Linear models provide a useful baseline when effects are roughly additive.
- Trees capture nonlinear boundaries; depth and minimum leaf size control flexibility.
- Use identical folds for comparisons, and keep preprocessing inside each candidate pipeline.
- Scikit-learn maximizes scores: `neg_mean_absolute_error` must be negated for reported MAE.
- The selected CV score is optimistic after trying many alternatives. Evaluate the frozen
  choice on a test set; use nested CV when estimating the entire selection procedure.

References: [linear models](https://scikit-learn.org/stable/modules/linear_model.html),
[trees](https://scikit-learn.org/stable/modules/tree.html),
[cross_validate](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.cross_validate.html),
and [GridSearchCV](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html).

## Example

```powershell
uv run python modules/04_machine_learning/04_models/example.py
```

A tiny generated plant-classification example searches tree depth using stratified
development folds. A disjoint test set is scored once after selection. The exercise
instead compares three regression candidates and returns fold-level MAE summaries.

## Exercises

Complete [validation model comparison](exercises/model_comparison/README.md), including
a dummy baseline, independent preprocessing per fold and reproducible fold ordering.

## Self-check

1. Why can an unrestricted tree have perfect training accuracy and poor validation accuracy?
2. Why must all candidates share validation folds?
3. What does a negative MAE scorer mean, and which direction is better?

## Done when

You can justify a model against its baseline, report validation variability, and distinguish
the selection score from a final estimate of generalization.
