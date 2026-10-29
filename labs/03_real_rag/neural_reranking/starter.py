"""Independent learner ranking implementation. See README for exact contracts."""

from collections.abc import Callable, Mapping, Sequence
from typing import Any

PairScorer = Callable[[list[tuple[str, str]]], Sequence[float]]


def rerank(
    query: str, candidates: list[dict[str, str]], scorer: PairScorer, k: int
) -> list[dict[str, Any]]:
    """Score pairs once, preserve IDs/text, finite scalar scores, tie by ascending ID."""
    raise NotImplementedError("Implement bounded candidate-only neural reranking")


def ranking_metrics(
    rankings: Mapping[str, Sequence[str]], qrels: Mapping[str, Mapping[str, int]], k: int
) -> dict[str, dict[str, float | None]]:
    """Full-candidate recall, top-k MRR/nDCG; no positive qrels => all None."""
    raise NotImplementedError("Implement graded per-query metrics without losing query identity")
