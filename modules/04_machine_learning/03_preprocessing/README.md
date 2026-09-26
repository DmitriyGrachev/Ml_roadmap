# Leakage-free preprocessing

## Goal

Fit missing-value handling, scaling, category encoding and the estimator as one pipeline.
Make predictions on new rows without relearning the preprocessing state.

## Java mental model

Think of a pipeline as a composed service whose fitted transformers own state. A scaler's
mean is learned data, unlike a stateless number-formatting utility. Computing it over
the whole dataset before validation leaks information.

## Python model

`ColumnTransformer` routes named columns to separate transformations. `Pipeline.fit`
learns transformations and the final estimator from training data. `predict` reuses that
state. Pass the complete pipeline to cross-validation so each fold learns independently.

## Key concepts

- Median imputation and standardization are suitable starting points for numeric features.
- Categorical missing values and unseen categories are different cases.
- Declare categorical column dtypes explicitly: an all-NaN column may otherwise look
  numeric and reject a string imputation value. The exercise uses `object` columns.
- `OneHotEncoder(handle_unknown="ignore")` represents unseen categories with zeros;
  this avoids a runtime error but does not guarantee good predictions.
- `keep_empty_features=True` preserves numeric columns missing throughout a training fold.
- Name columns explicitly and drop unspecified fields, including identifiers and targets.

References: [mixed columns](https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html),
[Pipeline](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html),
and [OneHotEncoder](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html).

## Example

```powershell
uv run python modules/04_machine_learning/03_preprocessing/example.py
```

The example demonstrates a numeric-only plant classifier and proves that its scaler
keeps its training mean when asked to predict a much larger new measurement. The exercise
adds independent categorical branches and a regression model.

## Exercises

Build the [mixed-feature park-visit pipeline](exercises/mixed_feature_pipeline/README.md).
Test missing numbers, a completely empty numeric training column and a new location type.

## Self-check

1. What is learned by an imputer, scaler and category encoder?
2. Why is `fit_transform` on validation data incorrect?
3. How can an identifier accidentally become a predictive shortcut?

## Done when

Your complete pipeline can be fitted independently inside every fold and accept missing
values and previously unseen categories without changing the caller's data.
