"""Learner geometry on arbitrary, noncentered feature matrices."""

import numpy as np
from numpy.typing import NDArray


def centered_ridge(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    alpha: float,
) -> tuple[NDArray[np.float64], float]:
    """Minimize sum squared residuals + alpha * ||w||²; b is unpenalized."""
    # TODO: center using train means; solve a system; reconstruct b.
    raise NotImplementedError("fit centered Ridge without inverse")


def principal_components(
    x: NDArray[np.float64],
    k: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Return train mean, k row eigenvectors, k descending sample eigenvalues."""
    # TODO: sample covariance denominator n-1; sort eigenpairs together.
    raise NotImplementedError("derive centered principal components")
