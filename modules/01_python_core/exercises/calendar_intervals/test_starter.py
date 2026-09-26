"""Behavioral checks for the calendar interval exercise."""

from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import Interval, merge_intervals


@pytest.mark.student_exercise
def test_merges_unsorted_overlaps_containment_duplicates_and_touching_edges() -> None:
    intervals = [
        Interval(630, 660),
        Interval(570, 610),
        Interval(600, 630),
        Interval(590, 600),
        Interval(570, 610),
        Interval(800, 840),
    ]
    assert exercise_call(merge_intervals, intervals) == [Interval(570, 660), Interval(800, 840)]


@pytest.mark.student_exercise
def test_disjoint_intervals_stay_separate_and_day_boundaries_are_valid() -> None:
    assert exercise_call(merge_intervals, (Interval(1439, 1440), Interval(0, 1))) == [
        Interval(0, 1),
        Interval(1439, 1440),
    ]


@pytest.mark.student_exercise
def test_empty_and_single_interval() -> None:
    assert exercise_call(merge_intervals, []) == []
    assert exercise_call(merge_intervals, [Interval(0, 1440)]) == [Interval(0, 1440)]


@pytest.mark.student_exercise
def test_deterministic_without_mutating_input_and_returns_a_fresh_list() -> None:
    source = [Interval(30, 60), Interval(0, 20)]
    before = source.copy()
    first = exercise_call(merge_intervals, source)
    assert first == exercise_call(merge_intervals, source)
    assert source == before
    assert first is not source
    first.clear()
    assert source == before


@pytest.mark.parametrize(
    ("start", "end"), [(-1, 5), (5, 5), (6, 5), (0, 1441), (True, 5), (0, 1.5)]
)
def test_invalid_endpoints(start: object, end: object) -> None:
    interval = Interval(cast(int, start), cast(int, end))
    with pytest.raises(ValueError, match="interval endpoints"):
        exercise_call(merge_intervals, [interval])
