"""Behavior checks for authorization, geometry and stable retrieval contracts."""

import math

import pytest

from roadmap_tools import exercise_call

from .starter import VectorDocument, vector_search

PUBLIC = frozenset({"public"})


def test_authorization_precedes_top_k_and_ties_use_document_id() -> None:
    docs = [
        VectorDocument("staff", (1.0, 0.0), frozenset({"staff"})),
        VectorDocument("garden-b", (0.6, 0.8), PUBLIC),
        VectorDocument("garden-a", (0.6, 0.8), PUBLIC),
        VectorDocument("closed", (1.0, 0.0), frozenset()),
    ]
    hits = exercise_call(vector_search, [1.0, 0.0], docs, roles=PUBLIC, top_k=2)
    assert [hit.document_id for hit in hits] == ["garden-a", "garden-b"]
    assert [hit.score for hit in hits] == pytest.approx([0.6, 0.6])
    assert exercise_call(vector_search, [1.0, 0.0], docs[::-1], roles=PUBLIC, top_k=2) == hits


def test_zero_vectors_negative_scores_and_large_k() -> None:
    docs = [
        VectorDocument("zero", (0.0, 0.0), PUBLIC),
        VectorDocument("opposite", (-2.0, 0.0), PUBLIC),
    ]
    hits = exercise_call(vector_search, [3.0, 0.0], docs, roles=PUBLIC, top_k=9)
    assert [(hit.document_id, hit.score) for hit in hits] == [("zero", 0.0), ("opposite", -1.0)]
    zero_query = exercise_call(vector_search, [0.0, 0.0], docs, roles=PUBLIC)
    assert [(hit.document_id, hit.score) for hit in zero_query] == [
        ("opposite", 0.0),
        ("zero", 0.0),
    ]


def test_extreme_finite_vectors_do_not_overflow_or_underflow() -> None:
    docs = [VectorDocument("tiny", (1e-300, 1e-300), PUBLIC)]
    hits = exercise_call(vector_search, [1e300, 1e300], docs, roles=PUBLIC)
    assert math.isfinite(hits[0].score)
    assert -1 <= hits[0].score <= 1
    assert hits[0].score == pytest.approx(1.0)


def test_empty_index_no_access_zero_k_and_input_preservation() -> None:
    query = [1.0, 0.0]
    docs = [VectorDocument("guide", (1.0, 0.0), PUBLIC)]
    original = docs.copy()
    assert exercise_call(vector_search, query, [], roles=PUBLIC) == ()
    assert exercise_call(vector_search, query, docs, roles=frozenset()) == ()
    assert exercise_call(vector_search, query, docs, roles=PUBLIC, top_k=0) == ()
    assert docs == original
    assert query == [1.0, 0.0]


@pytest.mark.parametrize("query", [[], [float("nan")], [float("inf")]])
def test_invalid_query_rejected_even_without_documents(query: list[float]) -> None:
    with pytest.raises(ValueError, match="query"):
        exercise_call(vector_search, query, [], roles=PUBLIC)


@pytest.mark.parametrize("embedding", [(1.0,), (float("nan"), 0.0), (float("inf"), 0.0)])
def test_corrupt_unauthorized_embedding_rejected_even_at_zero_k(
    embedding: tuple[float, ...],
) -> None:
    docs = [VectorDocument("staff", embedding, frozenset({"staff"}))]
    with pytest.raises(ValueError, match=r"embedding|dimension"):
        exercise_call(vector_search, [1.0, 0.0], docs, roles=PUBLIC, top_k=0)


@pytest.mark.parametrize("top_k", [-1, True])
def test_invalid_top_k_rejected(top_k: int) -> None:
    with pytest.raises(ValueError, match="top_k"):
        exercise_call(vector_search, [1.0], [], roles=PUBLIC, top_k=top_k)


def test_duplicate_or_blank_document_ids_rejected() -> None:
    for docs in [
        [VectorDocument("same", (1.0,), PUBLIC)] * 2,
        [VectorDocument("   ", (1.0,), PUBLIC)],
    ]:
        with pytest.raises(ValueError, match="document"):
            exercise_call(vector_search, [1.0], docs, roles=PUBLIC)


def test_invalid_role_names_rejected_in_either_side() -> None:
    with pytest.raises(ValueError, match="role"):
        exercise_call(vector_search, [1.0], [], roles=frozenset({""}))
    with pytest.raises(ValueError, match="role"):
        exercise_call(
            vector_search, [1.0], [VectorDocument("a", (1.0,), frozenset({" "}))], roles=PUBLIC
        )
