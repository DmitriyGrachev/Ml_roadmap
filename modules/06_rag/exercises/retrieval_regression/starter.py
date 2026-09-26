"""Student boundary for paired query-level retrieval regression checks."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class QueryJudgment:
    """A query and the complete known relevant-document set."""

    query_id: str
    relevant_ids: frozenset[str]


@dataclass(frozen=True)
class RegressionReport:
    """Macro recall over every judgment and the resulting release guard."""

    query_count: int
    baseline_mean: float
    candidate_mean: float
    regressed_queries: tuple[str, ...]
    passed: bool


def compare_retrieval(
    judgments: tuple[QueryJudgment, ...],
    baseline: dict[str, tuple[str, ...]],
    candidate: dict[str, tuple[str, ...]],
    *,
    k: int,
    max_query_drop: float = 0.0,
    max_mean_drop: float = 0.0,
) -> RegressionReport:
    """Compare recall at k for paired queries using complete denominators."""
    if type(k) is not int or k <= 0:
        raise ValueError("k must be a positive integer")
    for value in (max_query_drop, max_mean_drop):
        if type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 1:
            raise ValueError("drop bounds must be finite numbers in [0, 1]")
    ids: set[str] = set()
    for judgment in judgments:
        if not isinstance(judgment.query_id, str) or not judgment.query_id.strip():
            raise ValueError("query IDs must be nonblank strings")
        if judgment.query_id in ids:
            raise ValueError("query IDs must be unique")
        if any(
            not isinstance(doc_id, str) or not doc_id.strip() for doc_id in judgment.relevant_ids
        ):
            raise ValueError("relevant document IDs must be nonblank strings")
        ids.add(judgment.query_id)
    for rankings in (baseline, candidate):
        if any(query_id not in ids for query_id in rankings):
            raise ValueError("ranking keys must belong to judged queries")
        for ranking in rankings.values():
            if any(not isinstance(doc_id, str) or not doc_id.strip() for doc_id in ranking):
                raise ValueError("ranked document IDs must be nonblank strings")
    # TODO: deduplicate before cutoff, score every query, and apply both guards.
    raise NotImplementedError("paired retrieval regression guard")
