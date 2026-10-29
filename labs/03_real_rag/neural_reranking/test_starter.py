"""Learner boundaries only; literal scores test contracts, never model quality."""

import math
from importlib import import_module

import pytest

from roadmap_tools import exercise_call

s = import_module("labs.03_real_rag.neural_reranking.starter")


def test_pair_scores_preserve_identity_and_deterministic_ties() -> None:
    candidates = [{"id": "b", "text": "B"}, {"id": "a", "text": "A"}]
    seen = []

    def scorer(pairs: list[tuple[str, str]]) -> list[float]:
        seen.extend(pairs)
        return [0.4, 0.4]

    result = exercise_call(s.rerank, "Q", candidates, scorer, 8)
    assert seen == [("Q", "B"), ("Q", "A")]
    assert result == [dict(candidates[1], score=0.4), dict(candidates[0], score=0.4)]
    assert candidates == [{"id": "b", "text": "B"}, {"id": "a", "text": "A"}]


@pytest.mark.parametrize("scores", [[float("nan"), 1.0], [float("inf"), 0], [1], [[1], [2]]])
def test_scores_must_be_finite_aligned_scalars(scores: list[object]) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        exercise_call(
            s.rerank,
            "q",
            [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}],
            lambda pairs: scores,
            1,
        )


def test_empty_candidates_never_call_scorer() -> None:
    def forbidden(pairs: object) -> object:
        pytest.fail("No model call for absent candidates")

    assert exercise_call(s.rerank, "q", [], forbidden, 1) == []


@pytest.mark.parametrize("k", [0, -1, True])
def test_invalid_cutoffs(k: int) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        exercise_call(s.rerank, "q", [], lambda pairs: [], k)


def test_duplicate_candidate_ids_are_rejected() -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        exercise_call(s.rerank, "q", [{"id": "a", "text": "A"}] * 2, lambda pairs: [1, 2], 1)


def test_fully_worked_graded_metrics_and_missing_candidate() -> None:
    rankings = {"q1": ["b", "x", "a"], "q2": [], "q3": ["x"]}
    qrels = {"q1": {"a": 2, "b": 1, "c": 1}, "q2": {"z": 1}, "q3": {"x": 0}}
    result = exercise_call(s.ranking_metrics, rankings, qrels, 3)
    assert set(result) == set(rankings)
    assert result["q1"]["candidate_recall"] == pytest.approx(2 / 3)
    assert result["q1"]["mrr_at_k"] == 1
    assert result["q1"]["ndcg_at_k"] == pytest.approx(2.5 / (3 + 1 / math.log2(3) + 0.5))
    assert result["q2"] == dict.fromkeys(["candidate_recall", "mrr_at_k", "ndcg_at_k"], 0.0)
    assert result["q3"] == dict.fromkeys(["candidate_recall", "mrr_at_k", "ndcg_at_k"], None)


def test_candidate_recall_uses_full_pool_while_rank_metrics_use_cutoff() -> None:
    result = exercise_call(s.ranking_metrics, {"q": ["x", "a"]}, {"q": {"a": 2, "missing": 1}}, 1)
    assert result["q"] == {"candidate_recall": 0.5, "mrr_at_k": 0.0, "ndcg_at_k": 0.0}


@pytest.mark.parametrize(
    ("rankings", "qrels"),
    [
        ({"q": ["a", "a"]}, {"q": {"a": 1}}),
        ({"q": []}, {"other": {}}),
        ({"q": []}, {"q": {"a": -1}}),
    ],
)
def test_metric_identity_duplicates_and_negative_grades(rankings: object, qrels: object) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        exercise_call(s.ranking_metrics, rankings, qrels, 2)
