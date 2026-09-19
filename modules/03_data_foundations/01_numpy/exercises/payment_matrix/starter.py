"""Starter boundary for vectorized payment-matrix conversion."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def convert_amount_matrix(
    amounts: NDArray[np.float64], rates: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Convert a two-dimensional float64 amount matrix with one rate per currency.

    `amounts` has shape ``(record_count, currency_count)`` and `rates` has shape
    ``(currency_count,)``. Raise `ValueError` for invalid shapes. Inputs must remain
    unchanged; complete the conversion with broadcasting and without Python loops.
    """
    if amounts.ndim != 2:
        raise ValueError("amounts must be two-dimensional")
    if rates.ndim != 1:
        raise ValueError("rates must be one-dimensional")
    if amounts.shape[1] != rates.shape[0]:
        raise ValueError("rate vector must match the currency dimension")
    raise NotImplementedError("Implement matrix conversion with NumPy broadcasting")
