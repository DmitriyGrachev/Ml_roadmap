"""Greedy context packing with stable source order."""

# Error message wording is intentionally outside this exercise's contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import ContextSegment, PackedContext, pack_context

pytestmark = pytest.mark.student_exercise


def test_priority_selection_returns_selected_segments_in_source_order() -> None:
    low = ContextSegment("a", "Opening hours", 2, 1)
    high = ContextSegment("b", "Library access", 3, 9)
    middle = ContextSegment("c", "Map", 2, 5)
    assert exercise_call(pack_context, (low, high, middle), budget=6, reserved=1) == PackedContext(
        (high, middle), 5
    )


def test_priority_order_is_distinct_from_output_order() -> None:
    first = ContextSegment("a", "A", 2, 0)
    second = ContextSegment("b", "B", 2, 10)
    assert exercise_call(pack_context, (first, second), budget=4) == PackedContext(
        (first, second), 4
    )


def test_equal_priority_uses_input_order_and_does_not_optimize_knapsack() -> None:
    rows = (ContextSegment("a", "A", 3, 1), ContextSegment("b", "B", 2, 1))
    assert exercise_call(pack_context, rows, budget=3) == PackedContext((rows[0],), 3)


def test_oversized_segment_is_skipped_and_later_segments_still_fit() -> None:
    rows = (ContextSegment("a", "A", 9, 10), ContextSegment("b", "", 2, -1))
    assert exercise_call(pack_context, rows, budget=2) == PackedContext((rows[1],), 2)


def test_zero_capacity_and_empty_input() -> None:
    assert exercise_call(pack_context, (ContextSegment("a", "A", 1, 1),), budget=2, reserved=2) == (
        PackedContext((), 0)
    )
    assert exercise_call(pack_context, (), budget=0) == PackedContext((), 0)


def test_no_mutation_or_hidden_state() -> None:
    rows = (ContextSegment("b", "B", 1, 2), ContextSegment("a", "A", 1, 1))
    assert exercise_call(pack_context, rows, budget=1) == PackedContext((rows[0],), 1)
    assert exercise_call(pack_context, rows, budget=2) == PackedContext(rows, 2)
    assert rows[0].id == "b"


@pytest.mark.parametrize(("budget", "reserved"), [(-1, 0), (2, 3), (True, 0), (2, -1)])
def test_invalid_budgets(budget: object, reserved: object) -> None:
    with pytest.raises(ValueError):
        exercise_call(pack_context, (), budget=budget, reserved=reserved)


@pytest.mark.parametrize(
    "rows",
    [
        (ContextSegment("a", "A", 0, 1),),
        (ContextSegment(" ", "A", 1, 1),),
        (ContextSegment("a", "A", 1, 1), ContextSegment("a", "B", 1, 2)),
        (ContextSegment("a", "A", 1, True),),
    ],
)
def test_invalid_segments_are_rejected_even_with_zero_capacity(
    rows: tuple[ContextSegment, ...],
) -> None:
    with pytest.raises(ValueError):
        exercise_call(pack_context, rows, budget=0)
