"""Exact vector ranking with an explicit authorization boundary."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class VectorDocument:
    document_id: str
    embedding: tuple[float, ...]
    allowed_roles: frozenset[str]


@dataclass(frozen=True)
class VectorHit:
    document_id: str
    score: float


def vector_search(
    query: Sequence[float],
    documents: Sequence[VectorDocument],
    *,
    roles: frozenset[str],
    top_k: int = 3,
) -> tuple[VectorHit, ...]:
    """Validate the index, authorize candidates and rank by stable exact cosine.

    Zero-vector similarity is zero. A document is visible only when allowed_roles
    intersects roles; an empty role set never grants public access. See README.
    """
    # TODO: validate, filter before top-k, calculate stable scores, sort and truncate.
    raise NotImplementedError("Implement authorized vector search")
