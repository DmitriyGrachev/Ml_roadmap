"""Independent randomization units must stay in one arm."""

import math

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import UnitOutcome, aggregate_units

pytestmark = pytest.mark.student_exercise


def test_events_are_averaged_within_units_in_id_order() -> None:
    result = exercise_call(
        aggregate_units,
        ["u2", "u1", "u2", "u1", "u3"],
        ["B", "A", "B", "A", "A"],
        [4.0, 1.0, 8.0, 3.0, 7.0],
    )
    assert result == (
        UnitOutcome("u1", "A", 2.0, 2),
        UnitOutcome("u2", "B", 6.0, 2),
        UnitOutcome("u3", "A", 7.0, 1),
    )


def test_same_unit_cannot_receive_both_arms() -> None:
    with pytest.raises(ValueError, match=r"arm|assignment"):
        exercise_call(aggregate_units, ["u1", "u1"], ["A", "B"], [1.0, 2.0])


@pytest.mark.parametrize(
    ("ids", "arms", "outcomes"),
    [
        ([], [], []),
        (["u1"], [], [1.0]),
        (["u1"], ["C"], [1.0]),
        ([""], ["A"], [1.0]),
        (["u1"], ["A"], [math.nan]),
        (["u1"], ["A"], [math.inf]),
    ],
)
def test_invalid_experiment_events_rejected(
    ids: list[str],
    arms: list[str],
    outcomes: list[float],
) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(aggregate_units, ids, arms, outcomes)
