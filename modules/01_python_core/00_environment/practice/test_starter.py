"""Required student contracts; unfinished TODO is not a strict check pass."""

from typing import Any

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import count_long_labels

pytestmark = pytest.mark.student_exercise


def test_counts_stripped_labels_with_inclusive_boundary() -> None:
    assert exercise_call(count_long_labels, [" oak ", "pine", "elm", "  "], 3) == 3
    assert exercise_call(count_long_labels, [" oak ", "pine", "elm", "  "], 4) == 1


def test_empty_and_blank_input_return_zero() -> None:
    assert exercise_call(count_long_labels, [], 1) == 0
    assert exercise_call(count_long_labels, ["", "  ", "\t"], 1) == 0


@pytest.mark.parametrize("minimum", [0, -1, True, 2.0, "2"])
def test_invalid_minimum_is_rejected_even_for_empty_labels(minimum: Any) -> None:
    with pytest.raises(ValueError, match="minimum"):
        exercise_call(count_long_labels, [], minimum)


@pytest.mark.parametrize("labels", [["oak", 3], [None], "oak", ("oak",)])
def test_invalid_labels_are_rejected(labels: Any) -> None:
    with pytest.raises(ValueError, match="labels"):
        exercise_call(count_long_labels, labels, 3)


def test_input_unchanged_and_calls_independent() -> None:
    labels = [" oak ", "pine"]
    assert exercise_call(count_long_labels, labels, 4) == 1
    assert exercise_call(count_long_labels, labels, 4) == 1
    assert labels == [" oak ", "pine"]
