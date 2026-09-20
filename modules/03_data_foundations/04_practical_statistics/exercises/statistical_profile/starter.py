"""Starter boundary for descriptive statistics over transaction amounts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class StatisticalProfile:
    """Immutable descriptive statistics for the finite, present input values."""

    mean: float
    median: float
    variance: float
    standard_deviation: float
    p25: float
    p75: float
    p95: float


def describe_amounts(values: NDArray[np.float64]) -> StatisticalProfile:
    """Describe finite values after ignoring NaNs, without mutating ``values``.

    Use population variance and population standard deviation. Percentiles use NumPy's
    default linear interpolation. Raise ``ValueError`` for empty input, all-NaN input,
    or any positive or negative infinity.
    """
    raise NotImplementedError("Implement the statistical amount profile")
