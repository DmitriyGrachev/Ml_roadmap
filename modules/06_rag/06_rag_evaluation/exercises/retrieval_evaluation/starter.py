"""Evaluate every declared query, including missing retrieval runs."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryMetrics:
    query_id: str
    relevant_total: int
    retrieved_count: int
    recall_at_k: float
    reciprocal_rank: float
    ndcg_at_k: float


@dataclass(frozen=True)
class RetrievalEvaluation:
    per_query: tuple[QueryMetrics, ...]
    mean_recall_at_k: float
    mrr_at_k: float
    mean_ndcg_at_k: float


def evaluate_retrieval(
    judgments: Mapping[str, Mapping[str, int]],
    results: Mapping[str, Sequence[str]],
    *,
    k: int = 5,
) -> RetrievalEvaluation:
    """Join by query ID and report macro recall@k, truncated MRR and nDCG@k.

    Relevance grades are integers 0..3, with exponential gains for nDCG. Queries
    lacking positive judgments have zero metrics and remain in the denominator.
    """
    # TODO: validate, evaluate every judged query, aggregate unrounded metrics.
    raise NotImplementedError("Implement retrieval evaluation by query")
