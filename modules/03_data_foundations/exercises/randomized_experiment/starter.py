"""Student boundary for A/B event aggregation by randomized unit."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class UnitOutcome:
    unit_id: str
    arm: str
    mean_outcome: float
    count: int


def aggregate_units(
    unit_ids: Sequence[str], assignments: Sequence[str], outcomes: Sequence[float]
) -> tuple[UnitOutcome, ...]:
    """Return unit-level means in deterministic ID order."""
    # TODO: reject mixed assignments and nonfinite/misaligned inputs; group by unit.
    raise NotImplementedError("aggregate randomized experiment units")
