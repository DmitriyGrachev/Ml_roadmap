"""Hand-counted conveyor-sensor decisions; separate from the teacher fixture."""

# Error message wording is intentionally outside the contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import GroupSlice, grouped_slices

pytestmark = pytest.mark.student_exercise


def test_group_counts_order_and_conditional_rates() -> None:
    result = exercise_call(
        grouped_slices,
        (1, 0, 1, 0, 0, 1),
        (0, 1, 1, 0, 0, 1),
        ("cold", "cold", "warm", "cold", "cold", "cold"),
        groups=("warm", "cold", "new"),
    )
    assert result == (
        GroupSlice("warm", 1, 1, 0, 0, 0, 1.0, 1.0, None, 1.0),
        GroupSlice("cold", 5, 1, 1, 1, 2, 0.4, 0.5, 1 / 3, 0.5),
        GroupSlice("new", 0, 0, 0, 0, 0, None, None, None, None),
    )


def test_empty_data_keeps_expected_group() -> None:
    assert exercise_call(grouped_slices, (), (), (), groups=("future",)) == (
        GroupSlice("future", 0, 0, 0, 0, 0, None, None, None, None),
    )


def test_missing_denominator_differs_from_observed_zero() -> None:
    result = exercise_call(
        grouped_slices, (0, 1), (0, 0), ("cold", "warm"), groups=("cold", "warm")
    )
    assert result == (
        GroupSlice("cold", 1, 0, 0, 0, 1, 0.0, None, 0.0, None),
        GroupSlice("warm", 1, 0, 0, 1, 0, 0.0, 0.0, None, None),
    )


def test_same_inputs_are_unchanged_and_repeatable() -> None:
    actual, decisions, memberships, groups = (0, 1), (1, 0), ("x", "x"), ("x", "y")
    first = exercise_call(grouped_slices, actual, decisions, memberships, groups=groups)
    assert first == exercise_call(grouped_slices, actual, decisions, memberships, groups=groups)
    assert (actual, decisions, memberships, groups) == ((0, 1), (1, 0), ("x", "x"), ("x", "y"))


@pytest.mark.parametrize("groups", [(), ("x", "x"), ("",), (" ",)])
def test_invalid_group_space(groups: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        exercise_call(grouped_slices, (), (), (), groups=groups)


@pytest.mark.parametrize(
    ("actual", "decisions", "memberships"),
    [
        ((0,), (), ("x",)),
        ((), (), ("x",)),
        ((0,), (1,), ("unknown",)),
        ((2,), (0,), ("x",)),
        ((True,), (0,), ("x",)),
        ((0,), (False,), ("x",)),
        ((0,), (1.0,), ("x",)),
        (("1",), (0,), ("x",)),
    ],
)
def test_invalid_observations(
    actual: tuple[object, ...], decisions: tuple[object, ...], memberships: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError):
        exercise_call(grouped_slices, actual, decisions, memberships, groups=("x",))
