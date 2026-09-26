"""Student boundary for descriptive statistics over aligned finite measurements."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class PairSummary:
    """Undefined statistics use None rather than NaN or fabricated zero values."""

    count: int
    mean_x: float | None
    mean_y: float | None
    covariance: float | None
    correlation: float | None


def summarize_pairs(xs: Sequence[float], ys: Sequence[float]) -> PairSummary:
    """Filter aligned pairs together, then compute sample covariance and Pearson r."""
    # TODO: reject unequal lengths, keep jointly finite pairs, and handle degenerate data.
    raise NotImplementedError("summarize paired observations")
