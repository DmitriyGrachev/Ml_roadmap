"""Learner implementation: normalized observation weights, including zero weights."""

import numpy as np
from numpy.typing import NDArray


def weighted_objective_gradient(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    w: NDArray[np.float64],
    b: float,
    sample_weight: NDArray[np.float64],
    *,
    kind: str,
    l2: float,
) -> tuple[float, NDArray[np.float64], float]:
    """Return (objective, dw, db); see theory for reductions and valid inputs."""
    # TODO: validate shape/finite values, nonnegative l2 and weights with positive sum.
    # TODO: derive weighted MSE/BCE; stabilize BCE; never penalize b.
    raise NotImplementedError("derive normalized weighted objective and gradients")
