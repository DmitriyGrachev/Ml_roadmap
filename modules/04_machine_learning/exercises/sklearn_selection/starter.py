"""Learner-owned training selection and final holdout interpretation boundaries."""

import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.pipeline import Pipeline


def select_pipeline(
    frame: pd.DataFrame,
    labels: npt.NDArray[np.int64],
    groups: npt.NDArray[np.int64],
    *,
    seed: int,
) -> tuple[Pipeline, pd.DataFrame]:
    """Choose C using three group-disjoint folds and return train-refitted pipeline/CV table."""
    raise NotImplementedError("Implement train-only group CV with mixed-feature preprocessing")


def permutation_report(
    model: Pipeline,
    x_holdout: pd.DataFrame,
    y_holdout: npt.NDArray[np.int64],
    *,
    seed: int,
) -> pd.DataFrame:
    """Return heldout f1_macro permutation importance over original columns, five repeats."""
    raise NotImplementedError("Measure holdout importance without fitting or model selection")
