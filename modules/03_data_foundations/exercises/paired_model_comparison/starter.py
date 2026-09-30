"""Student boundary for independent-unit paired loss comparison."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class DifferenceEstimate:
    effect: float
    lower: float
    upper: float
    unit_count: int
    resample_count: int


def paired_difference(
    loss_a: Sequence[float],
    loss_b: Sequence[float],
    unit_ids: Sequence[str],
    *,
    seed: int,
    n_resamples: int,
    confidence: float,
) -> DifferenceEstimate:
    """Estimate mean per-unit (B minus A) loss and a clustered percentile interval."""
    # TODO: validate aligned finite losses and independent units; bootstrap whole units.
    raise NotImplementedError("paired model comparison")
