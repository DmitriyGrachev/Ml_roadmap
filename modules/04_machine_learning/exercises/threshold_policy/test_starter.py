"""Threshold-policy checks using synthetic weather alerts."""

# Error message wording is intentionally outside this exercise's contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import ThresholdChoice, choose_threshold

pytestmark = pytest.mark.student_exercise


def test_select_precision_then_recall_among_feasible_candidates() -> None:
    result = exercise_call(
        choose_threshold,
        (0.9, 0.8, 0.7, 0.6),
        (1, 0, 1, 0),
        thresholds=(0.6, 0.9, 0.7),
        min_recall=0.5,
        min_precision=0.5,
    )
    assert result == ThresholdChoice(0.9, 1.0, 0.5, 1)


def test_policy_can_force_a_lower_threshold_and_equality_is_positive() -> None:
    result = exercise_call(
        choose_threshold,
        (0.9, 0.8, 0.7, 0.6),
        (1, 0, 1, 0),
        thresholds=(0.9, 0.7, 0.6),
        min_recall=1.0,
        min_precision=0.6,
    )
    assert result == ThresholdChoice(0.7, 2 / 3, 1.0, 3)


def test_recall_breaks_equal_precision_ties() -> None:
    result = exercise_call(
        choose_threshold,
        (0.9, 0.7),
        (1, 1),
        thresholds=(0.9, 0.7),
        min_recall=0.0,
        min_precision=0.0,
    )
    assert result == ThresholdChoice(0.7, 1.0, 1.0, 2)


def test_identical_predictions_choose_highest_threshold_independent_of_order() -> None:
    result = exercise_call(
        choose_threshold,
        (0.9, 0.1),
        (1, 0),
        thresholds=(0.3, 0.8, 0.8, 0.5),
        min_recall=0.0,
        min_precision=0.0,
    )
    assert result == ThresholdChoice(0.8, 1.0, 1.0, 1)


def test_no_feasible_policy_returns_none() -> None:
    assert (
        exercise_call(
            choose_threshold,
            (0.2, 0.8),
            (1, 0),
            thresholds=(0.5,),
            min_recall=1.0,
            min_precision=1.0,
        )
        is None
    )


def test_no_positive_labels_prefers_fewer_alerts_after_zero_metrics() -> None:
    assert exercise_call(
        choose_threshold,
        (0.2, 0.8),
        (0, 0),
        thresholds=(0.0, 0.5, 1.0),
        min_recall=0.0,
        min_precision=0.0,
    ) == ThresholdChoice(1.0, 0.0, 0.0, 0)


def test_empty_observations_and_empty_candidates() -> None:
    assert exercise_call(
        choose_threshold, (), (), thresholds=(0.0, 1.0), min_recall=0.0, min_precision=0.0
    ) == ThresholdChoice(1.0, 0.0, 0.0, 0)
    assert (
        exercise_call(
            choose_threshold, (0.9,), (1,), thresholds=(), min_recall=0.0, min_precision=0.0
        )
        is None
    )


@pytest.mark.parametrize(
    ("scores", "actual", "thresholds", "min_recall", "min_precision"),
    [
        ((0.5,), (), (0.5,), 0.0, 0.0),
        ((float("nan"),), (1,), (0.5,), 0.0, 0.0),
        ((0.5,), (2,), (0.5,), 0.0, 0.0),
        ((0.5,), (True,), (0.5,), 0.0, 0.0),
        ((0.5,), (1,), (1.1,), 0.0, 0.0),
        ((0.5,), (1,), (0.5,), -0.1, 0.0),
        ((0.5,), (1,), (0.5,), 0.0, float("inf")),
    ],
)
def test_invalid_policy_inputs(
    scores: tuple[float, ...],
    actual: tuple[int, ...],
    thresholds: tuple[float, ...],
    min_recall: float,
    min_precision: float,
) -> None:
    with pytest.raises(ValueError):
        exercise_call(
            choose_threshold,
            scores,
            actual,
            thresholds=thresholds,
            min_recall=min_recall,
            min_precision=min_precision,
        )
