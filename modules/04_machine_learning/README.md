# Module 04 — Machine Learning

## Goal

Turn a prediction question into a defensible supervised-learning experiment. Use small,
local datasets about parks, plants, weather and sensors; no downloads or API keys are needed.

## Prerequisites

Complete Modules 01–03: Python core, production Python, and data foundations. You should be comfortable reading tabular data, checking data quality, and explaining leakage, class imbalance, and the limits of accuracy.

## Java mental model

An estimator looks like a service with `fit` and `predict`, but `fit` changes learned state.
Treat preprocessing and the estimator as one trainable component, with an explicit evaluation contract.

## Python model

Use scikit-learn estimators, `Pipeline`, `ColumnTransformer`, and explicit splitters.
Fit on training rows, select on validation folds, and inspect the reserved test set only
after the design and decision threshold are frozen. A seed is one part of reproducibility.

## Key concepts

| Lesson | Main question | Practice |
| --- | --- | --- |
| [01 Problem framing](01_problem_framing/README.md) | What is predicted, when, and against which baseline? | Write a prediction contract, then model comparison |
| [02 Validation](02_validation/README.md) | What must be unseen at evaluation time? | [Group-safe sensor split](02_validation/exercises/group_safe_split/README.md) |
| [03 Preprocessing](03_preprocessing/README.md) | What does the model learn from each fold? | [Mixed park-visit pipeline](03_preprocessing/exercises/mixed_feature_pipeline/README.md) |
| [04 Models](04_models/README.md) | Is extra complexity justified? | [Validation model comparison](04_models/exercises/model_comparison/README.md) |
| [05 Evaluation](05_evaluation/README.md) | Where and how does the model fail? | Error-slice interpretation, then evaluation report |
| [06 Reproducibility](06_reproducibility/README.md) | Can another person reproduce and trust the result? | [Reproducible evaluation report](06_reproducibility/exercises/evaluation_report/README.md) |

## Example

Run from the repository root after `uv sync`:

```powershell
uv run python modules/04_machine_learning/01_problem_framing/example.py
uv run pytest modules/04_machine_learning
uv run mypy -p modules.04_machine_learning
```

Every lesson has a standalone deterministic `example.py`. Numeric directory names work
with package-mode mypy; exercise tests use local package imports and pytest importlib mode.

## Exercises

All seven exercises are **Difficulty: Medium**, each approximately 45–75 minutes. Their
READMEs define validation rules, edge cases and focused test commands. Untouched boundaries
raise `NotImplementedError` and are expected-incomplete; an incorrect implementation fails.
Examples teach related mechanics on separate inputs and do not implement the exercise contracts.

Additional practice after the related lessons:

| Lesson connection | New practice |
| --- | --- |
| Validation | [Chronological weather split with a gap](exercises/time_series_split/README.md) |
| Evaluation | [Explicit-label wildlife classification report](exercises/multiclass_report/README.md) |
| Evaluation | [Weather-alert threshold policy](exercises/threshold_policy/README.md) |

## Self-check

1. Which fields are available at the exact prediction time?
2. Why can random row splits overestimate performance for repeated sensors?
3. Where must imputation and scaling run during cross-validation?
4. Why is the winning validation score not an unbiased final test estimate?
5. What must accompany a model artifact besides a random seed?

## Done when

You can run all six examples, complete the seven exercises, justify a baseline and split,
explain an error slice, and hand another person a versioned report with data provenance.
