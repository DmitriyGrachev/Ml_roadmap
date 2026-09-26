"""Hand-calculated metrics verify joins, rank discounts and full denominators."""

import math

import pytest

from roadmap_tools import exercise_call

from .starter import evaluate_retrieval


def test_join_cutoff_graded_gain_and_complete_denominator() -> None:
    judgments = {"q3": {"d": 0}, "q1": {"a": 3, "b": 1}, "q2": {"c": 2}}
    results = {"q3": ["d"], "q1": ["x", "b", "a"]}
    report = exercise_call(evaluate_retrieval, judgments, results, k=2)
    assert [row.query_id for row in report.per_query] == ["q1", "q2", "q3"]
    first = report.per_query[0]
    assert first.relevant_total == 2
    assert first.retrieved_count == 2
    assert first.recall_at_k == 0.5
    assert first.reciprocal_rank == 0.5
    expected_ndcg = (1 / math.log2(3)) / (7 + 1 / math.log2(3))
    assert first.ndcg_at_k == pytest.approx(expected_ndcg)
    assert report.per_query[1].retrieved_count == 0
    assert report.per_query[1].recall_at_k == report.per_query[1].ndcg_at_k == 0
    assert report.per_query[2].relevant_total == 0
    assert report.per_query[2].reciprocal_rank == 0
    assert report.mean_recall_at_k == pytest.approx(1 / 6)
    assert report.mrr_at_k == pytest.approx(1 / 6)
    assert report.mean_ndcg_at_k == pytest.approx(expected_ndcg / 3)


def test_relevance_is_query_specific_and_missing_results_are_not_dropped() -> None:
    report = exercise_call(evaluate_retrieval, {"one": {"a": 1}, "two": {"b": 1}}, {"one": ["b"]})
    assert report.mean_recall_at_k == report.mrr_at_k == report.mean_ndcg_at_k == 0
    assert len(report.per_query) == 2


def test_ideal_ranking_has_unit_ndcg_and_macro_average_is_not_pooled_recall() -> None:
    report = exercise_call(
        evaluate_retrieval,
        {"one": {"a": 3, "b": 2, "c": 1}, "two": {"x": 1}},
        {"one": ["a", "b", "c"], "two": []},
        k=9,
    )
    assert report.per_query[0].ndcg_at_k == pytest.approx(1)
    assert report.mean_recall_at_k == 0.5
    assert report.mrr_at_k == 0.5
    assert report.mean_ndcg_at_k == pytest.approx(0.5)


def test_all_empty_judgments_are_explicit_zero_and_inputs_unchanged() -> None:
    judgments: dict[str, dict[str, int]] = {"a": {}, "b": {"doc": 0}}
    results = {"a": ["unknown"], "b": []}
    report = exercise_call(evaluate_retrieval, judgments, results, k=1)
    assert report.mean_recall_at_k == report.mrr_at_k == report.mean_ndcg_at_k == 0
    assert judgments == {"a": {}, "b": {"doc": 0}}
    assert results == {"a": ["unknown"], "b": []}


def test_duplicate_results_beyond_cutoff_are_rejected() -> None:
    with pytest.raises(ValueError, match="document"):
        exercise_call(evaluate_retrieval, {"q": {"a": 1}}, {"q": ["a", "b", "b"]}, k=1)


@pytest.mark.parametrize("k", [0, -1, True])
def test_invalid_cutoff_rejected(k: int) -> None:
    with pytest.raises(ValueError, match="k"):
        exercise_call(evaluate_retrieval, {"q": {}}, {}, k=k)


@pytest.mark.parametrize("grade", [-1, 4, True])
def test_invalid_relevance_grade_rejected(grade: int) -> None:
    with pytest.raises(ValueError, match="grade"):
        exercise_call(evaluate_retrieval, {"q": {"a": grade}}, {})


def test_empty_or_unknown_query_metadata_rejected() -> None:
    cases: list[tuple[dict[str, dict[str, int]], dict[str, list[str]]]] = [
        ({}, {}),
        ({"": {}}, {}),
        ({"q": {}}, {"other": []}),
    ]
    for judgments, results in cases:
        with pytest.raises(ValueError, match="query"):
            exercise_call(evaluate_retrieval, judgments, results)


def test_invalid_document_ids_rejected_in_judgments_and_results() -> None:
    with pytest.raises(ValueError, match="document"):
        exercise_call(evaluate_retrieval, {"q": {"": 1}}, {})
    with pytest.raises(ValueError, match="document"):
        exercise_call(evaluate_retrieval, {"q": {}}, {"q": [" "]})
