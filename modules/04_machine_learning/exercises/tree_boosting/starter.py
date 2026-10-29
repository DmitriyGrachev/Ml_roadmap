"""Learner classification split and transferable residual boosting predictor."""

from typing import Any

import numpy as np
from numpy.typing import NDArray


def best_gini_split(
    x: NDArray[np.float64],
    y: NDArray[np.int64],
) -> tuple[float | None, float]:
    """Return lowest-threshold minimizing weighted child Gini; constant x -> None."""
    raise NotImplementedError("enumerate classification thresholds and weighted Gini")


def boost_predict(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    validation_x: NDArray[np.float64],
    validation_y: NDArray[np.float64],
    query_x: NDArray[np.float64],
    *,
    steps: int,
    rate: float,
) -> dict[str, Any]:
    """Return curves, earliest validation-selected step, and its query predictions."""
    # TODO: include step zero; fit max_depth=1 regressors only to train residuals.
    # query_x has no labels: selection must use validation, never query outcomes.
    raise NotImplementedError("fit residual ensemble and select by validation")
