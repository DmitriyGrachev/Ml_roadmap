"""Compare regression candidates on common development folds."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ModelScore:
    name: str
    fold_mae: tuple[float, ...]
    mean_mae: float
    std_mae: float


def compare_regressors(
    features: pd.DataFrame,
    target: pd.Series,
    folds: int = 4,
    seed: int = 42,
) -> list[ModelScore]:
    """Compare baseline, ridge and tree on shared shuffled KFold development splits.

    Return positive per-fold MAE and population summary statistics, sorted by
    (mean_mae, name). See the README for exact candidates and validation rules.
    """
    raise NotImplementedError("Implement the validation model comparison")
