"""Source-capped deterministic evidence selection."""

# Error message wording is intentionally outside this exercise's contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import Evidence, select_evidence

pytestmark = pytest.mark.student_exercise


def test_document_cap_prevents_one_source_from_filling_context() -> None:
    rows = (
        Evidence("a1", "a", 0.9),
        Evidence("a2", "a", 0.8),
        Evidence("b1", "b", 0.7),
        Evidence("c1", "c", 0.6),
    )
    assert exercise_call(select_evidence, rows, limit=3, per_document=1) == (
        rows[0],
        rows[2],
        rows[3],
    )


def test_ties_use_document_then_chunk_id_independent_of_input_order() -> None:
    rows = (Evidence("b", "z", 1.0), Evidence("c", "a", 1.0), Evidence("a", "a", 1.0))
    expected = (rows[2], rows[1], rows[0])
    assert exercise_call(select_evidence, rows, limit=3, per_document=2) == expected
    assert (
        exercise_call(select_evidence, tuple(reversed(rows)), limit=3, per_document=2) == expected
    )


def test_greedy_result_can_be_shorter_than_limit_and_accepts_negative_scores() -> None:
    rows = (Evidence("b", "a", -0.5), Evidence("a", "a", -0.2))
    assert exercise_call(select_evidence, rows, limit=5, per_document=1) == (rows[1],)


def test_limit_is_applied_after_source_cap() -> None:
    rows = (Evidence("a", "d", 3.0), Evidence("b", "d", 2.0), Evidence("c", "e", 1.0))
    assert exercise_call(select_evidence, rows, limit=2, per_document=2) == rows[:2]


def test_zero_limit_and_empty_candidates() -> None:
    assert exercise_call(select_evidence, (Evidence("a", "d", 1.0),), limit=0) == ()
    assert exercise_call(select_evidence, (), limit=3) == ()


def test_selection_does_not_modify_candidates() -> None:
    rows = (Evidence("low", "a", 0.0), Evidence("high", "b", 1.0))
    assert exercise_call(select_evidence, rows, limit=1) == (rows[1],)
    assert rows == (Evidence("low", "a", 0.0), Evidence("high", "b", 1.0))


@pytest.mark.parametrize(("limit", "per_document"), [(-1, 1), (1, 0), (True, 1)])
def test_invalid_limits(limit: object, per_document: object) -> None:
    with pytest.raises(ValueError):
        exercise_call(select_evidence, (), limit=limit, per_document=per_document)


@pytest.mark.parametrize(
    "rows",
    [
        (Evidence("a", "d", float("nan")),),
        (Evidence("a", " ", 1.0),),
        (Evidence("a", "d", 1.0), Evidence("a", "e", 0.0)),
    ],
)
def test_invalid_candidates_even_with_zero_limit(rows: tuple[Evidence, ...]) -> None:
    with pytest.raises(ValueError):
        exercise_call(select_evidence, rows, limit=0)
