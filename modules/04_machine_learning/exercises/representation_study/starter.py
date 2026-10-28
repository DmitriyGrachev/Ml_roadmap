"""Student inverse map: recover feature coordinates from component scores."""

import numpy as np
from numpy.typing import NDArray


def reconstruct_from_components(
    scores: NDArray[np.float64],
    components: NDArray[np.float64],
    mean: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Return the finite (n, p) reconstruction; see README for the contract."""
    raise NotImplementedError("Implement the inverse projection without fitting a model")
