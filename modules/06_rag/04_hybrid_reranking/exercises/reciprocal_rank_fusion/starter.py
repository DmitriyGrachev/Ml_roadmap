"""Merge independently authorized retrieval lists using ranks, not raw scores."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class FusedHit:
    document_id: str
    score: float


def fuse_rankings(
    rankings: Sequence[Sequence[str]],
    *,
    weights: Sequence[float] | None = None,
    rank_constant: float = 60.0,
    top_k: int = 5,
) -> tuple[FusedHit, ...]:
    """Return weighted one-based RRF scores with stable document-ID ties.

    Inputs are already authorized. Reject repeated IDs within one ranking; an ID
    appearing in distinct rankings legitimately accumulates contributions.
    """
    # TODO: validate all lists, accumulate positive-weight contributions, sort.
    raise NotImplementedError("Implement reciprocal rank fusion")
