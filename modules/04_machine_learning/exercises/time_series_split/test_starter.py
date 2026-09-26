"""Contracts for a chronological environmental-measurement split."""

# Error message wording is intentionally outside this exercise's contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import Measurement, TemporalSplit, chronological_split

pytestmark = pytest.mark.student_exercise


def test_sort_then_reserve_a_gap_without_leaking_future_rows() -> None:
    rows = tuple(Measurement(str(i), i, float(i)) for i in [5, 1, 4, 0, 3, 2])
    result = exercise_call(chronological_split, rows, train_size=2, test_size=2, gap=1)
    assert result == TemporalSplit(
        (Measurement("0", 0, 0.0), Measurement("1", 1, 1.0)),
        (Measurement("3", 3, 3.0), Measurement("4", 4, 4.0)),
    )


def test_zero_gap_and_unused_tail() -> None:
    rows = tuple(Measurement(str(i), i, 10.0) for i in range(4))
    assert exercise_call(chronological_split, rows, train_size=1, test_size=2) == TemporalSplit(
        rows[:1], rows[1:3]
    )


def test_input_order_and_records_are_unchanged() -> None:
    rows = (Measurement("late", 20, -2.0), Measurement("early", 10, 2.0))
    before = tuple(rows)
    first = exercise_call(chronological_split, rows, train_size=1, test_size=1)
    assert rows == before
    assert first == exercise_call(chronological_split, rows, train_size=1, test_size=1)
    assert first.train[0].id == "early"


@pytest.mark.parametrize(
    ("train_size", "test_size", "gap"),
    [(0, 1, 0), (1, 0, 0), (1, 1, -1), (True, 1, 0), (1, 1, 0.5)],
)
def test_invalid_window_parameters(train_size: object, test_size: object, gap: object) -> None:
    rows = tuple(Measurement(str(i), i, 1.0) for i in range(10))
    with pytest.raises(ValueError):
        exercise_call(
            chronological_split, rows, train_size=train_size, test_size=test_size, gap=gap
        )


def test_not_enough_rows_including_gap() -> None:
    with pytest.raises(ValueError):
        exercise_call(
            chronological_split,
            (Measurement("a", 1, 0.0), Measurement("b", 2, 1.0)),
            train_size=1,
            test_size=1,
            gap=1,
        )


def test_validation_includes_the_unused_tail() -> None:
    rows = (Measurement("a", 1, 0.0), Measurement("b", 2, 1.0), Measurement("c", 3, float("inf")))
    with pytest.raises(ValueError):
        exercise_call(chronological_split, rows, train_size=1, test_size=1)


@pytest.mark.parametrize(
    "rows",
    [
        (Measurement("a", 1, 1.0), Measurement("b", 1, 2.0)),
        (Measurement("a", 1, 1.0), Measurement("a", 2, 2.0)),
        (Measurement(" ", 1, 1.0), Measurement("b", 2, 2.0)),
        (Measurement("a", 1, float("nan")), Measurement("b", 2, 2.0)),
        (Measurement("a", True, 1.0), Measurement("b", 2, 2.0)),
    ],
)
def test_ambiguous_or_invalid_measurements(rows: tuple[Measurement, ...]) -> None:
    with pytest.raises(ValueError):
        exercise_call(chronological_split, rows, train_size=1, test_size=1)
