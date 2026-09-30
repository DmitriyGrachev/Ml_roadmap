"""Student-owned vector update; intentionally not implemented."""

import numpy as np
from numpy.typing import NDArray


def gradient_step(
    weights: NDArray[np.float64], gradient: NDArray[np.float64], rate: float
) -> NDArray[np.float64]:
    """Validate finite matching nonempty 1-D arrays and return a fresh descent update."""
    raise NotImplementedError("Implement the vector update and its input contract")
