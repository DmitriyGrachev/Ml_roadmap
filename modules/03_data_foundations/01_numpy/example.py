"""Broadcast support-response times across two SLA thresholds."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def compare_response_times_to_slas() -> NDArray[np.bool_]:
    """Return one compliance row per SLA without a Python loop."""
    response_minutes = np.array([8.0, 18.0, 35.0, 70.0], dtype=np.float64)
    sla_minutes = np.array([15.0, 45.0], dtype=np.float64)[:, np.newaxis]
    return response_minutes <= sla_minutes


def main() -> None:
    """Print the deterministic broadcast comparison."""
    print(compare_response_times_to_slas())


if __name__ == "__main__":
    main()
