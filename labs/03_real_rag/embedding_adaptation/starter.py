"""Independent learner data and contrastive optimization boundaries."""

from typing import Any


def make_triples(
    queries: list[dict[str, Any]], corpus: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Emit query_id/query/positive_id/positive/negative_id/negative/family/split rows.

    Known positives (including same normalized text under another ID) cannot be
    negatives. Deduplicate positives and repeated triples; reject unknown IDs.
    """
    raise NotImplementedError("Create independently annotated hard-negative triples")


def split_queries(queries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Return train/dev/holdout from explicit split labels; reject all family/query leaks."""
    raise NotImplementedError("Enforce query identity, text and family disjointness")


def fit_encoder(model: Any, triples: list[dict[str, str]], *, steps: int, seed: int) -> Any:
    """Train actual SentenceTransformer using cosine TripletLoss(margin=0.2).

    Tokenize query/positive/negative separately, align rows, backward, optimizer.step;
    return model. CPU, deterministic seed, steps 1..20, batch at most 8.
    """
    raise NotImplementedError("Implement real bounded contrastive optimization")
