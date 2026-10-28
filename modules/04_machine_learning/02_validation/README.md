# Validation that matches the prediction setting

Начните с [разобранной теории validation](theory.md), затем запустите пример и переходите к упражнению.

## Goal

Separate model fitting, design decisions and the final estimate of generalization.
Choose the split according to what will be new: rows, devices, sites or future time.

## Java mental model

A random unit-test fixture is not a realistic production boundary. Repeated measurements
from one sensor resemble cached state: sharing that sensor across partitions can make
the task easier than deployment to a new sensor.

## Python model

Reserve a test set first. Use the remaining development data for training and validation
or cross-validation. Use `GroupShuffleSplit`/`GroupKFold` for unseen entities,
`TimeSeriesSplit` for ordered observations, and stratification for suitable independent
classification rows. A group split alone does not enforce time order.

## Key concepts

- Each validation score must use a model and preprocessing fitted without that fold.
- Test results do not guide feature choice, hyperparameters or threshold tuning.
- Group fractions describe numbers of groups, not necessarily numbers of rows.
- A temporal gap can separate training observations from labels that overlap the next period.
- Sorting by time before a random shuffle does not create a temporal split.

References: [cross-validation strategies](https://scikit-learn.org/stable/modules/cross_validation.html),
[group splitting](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html),
and [common leakage pitfalls](https://scikit-learn.org/stable/common_pitfalls.html).

## Example

```powershell
uv run python modules/04_machine_learning/02_validation/example.py
```

The weather example first reserves four future days, then creates expanding validation
windows with a one-day gap on earlier observations. It intentionally does not implement
the exercise's group assignment procedure.

## Exercises

Complete the [group-safe sensor split](exercises/group_safe_split/README.md), including
uneven group sizes, duplicate row indexes and invalid split fractions.

## Self-check

1. Is the deployment target tomorrow on existing sensors or readings from unseen sensors?
2. What leaks if the same physical device appears in train and validation?
3. When must the test set be reserved before further experimentation?

## Done when

You can state which generalization question your split answers and demonstrate that the
partitions respect its group or temporal boundary.
