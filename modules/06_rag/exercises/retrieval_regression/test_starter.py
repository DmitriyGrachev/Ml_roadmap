"""Paired query evaluation with complete denominators."""

# Error message wording is intentionally outside this exercise's contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import QueryJudgment, compare_retrieval

pytestmark = pytest.mark.student_exercise


def test_query_regression_is_not_hidden_by_another_query_improvement() -> None:
    judgments = (
        QueryJudgment("hours", frozenset({"a", "b"})),
        QueryJudgment("map", frozenset({"c"})),
    )
    result = exercise_call(
        compare_retrieval,
        judgments,
        {"hours": ("a", "b")},
        {"hours": ("a",), "map": ("c",)},
        k=2,
        max_query_drop=0.0,
        max_mean_drop=0.0,
    )
    assert result.query_count == 2
    assert result.baseline_mean == 0.5
    assert result.candidate_mean == 0.75
    assert result.regressed_queries == ("hours",)
    assert result.passed is False


def test_missing_queries_and_empty_judgments_stay_in_macro_denominator() -> None:
    judgments = (
        QueryJudgment("a", frozenset({"x"})),
        QueryJudgment("b", frozenset({"y"})),
        QueryJudgment("empty", frozenset()),
    )
    result = exercise_call(compare_retrieval, judgments, {"a": ("x",)}, {}, k=1)
    assert result.query_count == 3
    assert result.baseline_mean == pytest.approx(1 / 3)
    assert result.candidate_mean == 0.0
    assert result.regressed_queries == ("a",)


def test_duplicates_are_removed_before_truncating_top_k() -> None:
    judgment = (QueryJudgment("q", frozenset({"a", "b"})),)
    result = exercise_call(
        compare_retrieval, judgment, {"q": ("a", "a", "b")}, {"q": ("b", "a")}, k=2
    )
    assert result.baseline_mean == result.candidate_mean == 1.0
    assert result.regressed_queries == ()
    assert result.passed is True


def test_exact_drop_boundaries_pass() -> None:
    judgment = (QueryJudgment("q", frozenset({"a", "b"})),)
    result = exercise_call(
        compare_retrieval,
        judgment,
        {"q": ("a", "b")},
        {"q": ("a",)},
        k=2,
        max_query_drop=0.5,
        max_mean_drop=0.5,
    )
    assert result.regressed_queries == ()
    assert result.passed is True


def test_mean_policy_can_fail_when_per_query_policy_passes() -> None:
    judgment = (QueryJudgment("q", frozenset({"a", "b"})),)
    result = exercise_call(
        compare_retrieval,
        judgment,
        {"q": ("a", "b")},
        {"q": ("a",)},
        k=2,
        max_query_drop=0.5,
        max_mean_drop=0.25,
    )
    assert result.regressed_queries == ()
    assert result.passed is False


def test_top_k_does_not_count_relevant_documents_below_cutoff() -> None:
    judgment = (QueryJudgment("q", frozenset({"a"})),)
    result = exercise_call(compare_retrieval, judgment, {}, {"q": ("x", "a")}, k=1)
    assert result.candidate_mean == 0.0
    assert result.passed is True


def test_empty_evaluation_has_zero_means_and_passes() -> None:
    result = exercise_call(compare_retrieval, (), {}, {}, k=1)
    assert (result.query_count, result.baseline_mean, result.candidate_mean) == (0, 0.0, 0.0)
    assert result.regressed_queries == ()
    assert result.passed is True


def test_regressions_are_sorted_and_inputs_are_unchanged() -> None:
    judgments = (QueryJudgment("z", frozenset({"a"})), QueryJudgment("b", frozenset({"a"})))
    baseline = {"z": ("a",), "b": ("a",)}
    result = exercise_call(compare_retrieval, judgments, baseline, {}, k=1)
    assert result.regressed_queries == ("b", "z")
    assert baseline == {"z": ("a",), "b": ("a",)}


@pytest.mark.parametrize(
    ("judgments", "baseline", "candidate"),
    [
        ((QueryJudgment("q", frozenset()), QueryJudgment("q", frozenset())), {}, {}),
        ((QueryJudgment("q", frozenset()),), {"unknown": ()}, {}),
        ((QueryJudgment("q", frozenset()),), {}, {"q": (" ",)}),
        ((QueryJudgment("q", frozenset({" "})),), {}, {}),
    ],
)
def test_invalid_judgments_or_rankings(
    judgments: tuple[QueryJudgment, ...],
    baseline: dict[str, tuple[str, ...]],
    candidate: dict[str, tuple[str, ...]],
) -> None:
    with pytest.raises(ValueError):
        exercise_call(compare_retrieval, judgments, baseline, candidate, k=1)


@pytest.mark.parametrize(
    ("k", "max_query_drop", "max_mean_drop"),
    [(0, 0.0, 0.0), (1, -0.1, 0.0), (1, 0.0, float("nan"))],
)
def test_invalid_policy(k: int, max_query_drop: float, max_mean_drop: float) -> None:
    with pytest.raises(ValueError):
        exercise_call(
            compare_retrieval,
            (),
            {},
            {},
            k=k,
            max_query_drop=max_query_drop,
            max_mean_drop=max_mean_drop,
        )
