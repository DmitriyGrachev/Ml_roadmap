"""Student boundary for a complete, paired offline release comparison."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    slice_name: str
    passed: bool


@dataclass(frozen=True)
class SliceComparison:
    slice_name: str
    count: int
    baseline_rate: float
    candidate_rate: float


@dataclass(frozen=True)
class GateReport:
    accepted: bool
    slices: tuple[SliceComparison, ...]
    reasons: tuple[str, ...]


def evaluate_release(
    baseline: Sequence[CaseResult],
    candidate: Sequence[CaseResult],
    *,
    min_cases_per_slice: int = 2,
    max_regression: float = 0.0,
) -> GateReport:
    """Validate a paired evaluation and enforce the README's per-slice policy."""
    # TODO: align case IDs, validate complete coverage, then compare every slice.
    raise NotImplementedError("evaluate paired release results")
