"""Student boundary for deterministic evidence selection with source caps."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Evidence:
    """A retrieved chunk whose authorization has already been checked."""

    chunk_id: str
    document_id: str
    score: float


def select_evidence(
    candidates: tuple[Evidence, ...],
    *,
    limit: int,
    per_document: int = 1,
) -> tuple[Evidence, ...]:
    """Rank candidates and greedily enforce the per-document cap."""
    if type(limit) is not int or limit < 0:
        raise ValueError("limit must be a nonnegative integer")
    if type(per_document) is not int or per_document <= 0:
        raise ValueError("per_document must be a positive integer")
    ids: set[str] = set()
    for item in candidates:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (item.chunk_id, item.document_id)
        ):
            raise ValueError("chunk and document IDs must be nonblank strings")
        if item.chunk_id in ids:
            raise ValueError("chunk IDs must be unique")
        if type(item.score) not in (int, float) or not isfinite(item.score):
            raise ValueError("scores must be finite numbers")
        ids.add(item.chunk_id)
    # TODO: rank, cap per source, and stop at the requested global limit.
    raise NotImplementedError("diversify retrieved evidence")
