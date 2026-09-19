"""Show why a median can summarize support latency more robustly than a mean."""

from __future__ import annotations

import numpy as np


def median_response_latency() -> float:
    """Return the median minutes for a batch containing one large outlier."""
    latency_minutes = np.array([8.0, 10.0, 11.0, 14.0, 300.0], dtype=np.float64)
    return float(np.median(latency_minutes))


def main() -> None:
    """Print the deterministic robust latency summary."""
    print(median_response_latency())


if __name__ == "__main__":
    main()
