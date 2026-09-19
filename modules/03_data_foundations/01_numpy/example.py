"""Vectorize a small support-cost conversion without Python loops."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def convert_support_costs() -> NDArray[np.float64]:
    """Convert two teams' USD support costs into EUR and GBP reporting values."""
    costs_usd = np.array([[10.0, 10.0], [20.0, 20.0]], dtype=np.float64)
    reporting_rates = np.array([1.2, 0.9], dtype=np.float64)
    return costs_usd * reporting_rates


def main() -> None:
    """Print the deterministic broadcast conversion."""
    print(convert_support_costs())


if __name__ == "__main__":
    main()
