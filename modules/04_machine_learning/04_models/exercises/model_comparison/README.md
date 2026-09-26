# Validation model comparison

Difficulty: Medium

Estimated time: 60–75 minutes. Prerequisites: validation, preprocessing and models lessons.

A cycling club wants to predict journey duration from numeric route measurements.
Compare a dummy baseline, regularized linear model and small tree on development data.
The function deliberately receives no test set: the test result cannot drive this selection.

## Contract

Implement `compare_regressors` and return the supplied immutable `ModelScore` records.

1. Require a nonempty numeric DataFrame with at least one feature and a numeric Series
   of the same length. Match rows **positionally**, regardless of index labels. Targets
   must be finite. Features may contain NaN, but not infinity or a completely missing column.
   Require unique nonempty string feature names, `2 <= folds <= len(target)` and a
   nonnegative integer seed. Reject invalid input with `ValueError` naming the relevant
   `feature`, `target`, `fold`, `seed` or input `length`/`empty` condition.
2. Compare exactly these candidates:

   | Name | Estimator |
   | --- | --- |
   | `baseline` | `DummyRegressor(strategy="mean")` |
   | `ridge` | Pipeline: median SimpleImputer, StandardScaler, Ridge(alpha=1.0, solver="svd") |
   | `tree` | Pipeline: median SimpleImputer, DecisionTreeRegressor(max_depth=3, min_samples_leaf=2, random_state=seed) |

   Both imputers use `keep_empty_features=True` so a feature missing within one fold
   does not disappear. Fit complete pipelines inside the CV operation.
3. Use the same `KFold(n_splits=folds, shuffle=True, random_state=seed)` partitions for
   all candidates and `cross_validate` with `scoring="neg_mean_absolute_error"`,
   `error_score="raise"`, `n_jobs=1`. Do not fit on the complete frame before CV.
4. Negate the returned scores. Store native floats in `fold_mae` in splitter order.
   Report their arithmetic mean and population standard deviation (`ddof=0`).
   Sort results by ascending `(mean_mae, name)`; do not round internally.
5. Never mutate the features or targets. Do not include elapsed timings in this
   deterministic result and do not use global random state.

The synthetic outlier test is intentional: a linear model may extrapolate badly on a
held-out extreme. The correct answer is not required to declare any model universally best.

## Edge cases

Missing features, a validation outlier, constant targets and ties, shuffled indexes,
invalid fold counts, nonfinite targets, an all-missing feature and repeated seeded runs.

## Run

```powershell
uv run pytest modules/04_machine_learning/04_models/exercises/model_comparison -q
```

Done when all candidate scores are comparable and reproducible, and you can explain why
their standard deviation is descriptive fold variability rather than a confidence interval.
