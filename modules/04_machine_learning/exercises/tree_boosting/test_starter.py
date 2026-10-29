"""Catch wrong Gini weights/ties and use of last instead of selected ensemble."""

from typing import Any

import numpy as np
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import best_gini_split, boost_predict

pytestmark = pytest.mark.student_exercise


def test_gini_split_uses_weighted_children() -> None:
    threshold, score = exercise_call(
        best_gini_split, np.array([0.0, 1.0, 2.0, 3.0]), np.array([0, 0, 1, 1])
    )
    assert threshold == pytest.approx(1.5)
    assert score == pytest.approx(0.0)


def test_equal_scores_choose_smallest_threshold_and_constant_feature_has_no_split() -> None:
    threshold, score = exercise_call(
        best_gini_split, np.array([0.0, 1.0, 2.0]), np.array([0, 1, 0])
    )
    assert threshold == pytest.approx(0.5)
    assert score == pytest.approx(1 / 3)
    threshold, score = exercise_call(best_gini_split, np.ones(3), np.array([0, 1, 0]))
    assert threshold is None
    assert score == pytest.approx(4 / 9)


def test_duplicate_values_do_not_create_empty_child() -> None:
    threshold, score = exercise_call(
        best_gini_split, np.array([1.0, 1.0, 3.0, 3.0]), np.array([2, 2, 4, 4])
    )
    assert threshold == pytest.approx(2.0)
    assert score == pytest.approx(0.0)


def test_boosting_fits_train_residuals_and_predicts_unseen_queries() -> None:
    result = exercise_call(
        boost_predict,
        np.array([0.0, 1.0, 2.0, 3.0]),
        np.array([0.0, 0.0, 8.0, 8.0]),
        np.array([0.5, 2.5]),
        np.array([0.0, 8.0]),
        np.array([-0.5, 4.0]),
        steps=3,
        rate=0.5,
    )
    np.testing.assert_allclose(result["train_mse"], [16.0, 4.0, 1.0, 0.25])
    np.testing.assert_allclose(result["validation_mse"], [16.0, 4.0, 1.0, 0.25])
    assert result["selected_step"] == 3
    np.testing.assert_allclose(result["query_predictions"], [0.5, 7.5])


def test_validation_can_select_baseline_despite_improving_train_error() -> None:
    result = exercise_call(
        boost_predict,
        np.array([0.0, 1.0, 2.0, 3.0]),
        np.array([0.0, 0.0, 8.0, 8.0]),
        np.array([0.5, 2.5]),
        np.array([4.0, 4.0]),
        np.array([-0.5, 4.0]),
        steps=3,
        rate=0.5,
    )
    assert result["selected_step"] == 0
    np.testing.assert_allclose(result["query_predictions"], [4.0, 4.0])
    assert result["train_mse"][-1] < result["train_mse"][0]


def test_validation_selects_unique_intermediate_snapshot_for_query_predictions() -> None:
    # Starting from 4, each half-rate stump halves the residual to targets 0/8:
    # predictions are [4,4], [2,6], [1,7], [0.5,7.5]. Validation wants [2,6].
    result = exercise_call(
        boost_predict,
        np.array([0.0, 1.0, 2.0, 3.0]),
        np.array([0.0, 0.0, 8.0, 8.0]),
        np.array([0.5, 2.5]),
        np.array([2.0, 6.0]),
        np.array([-0.5, 4.0]),
        steps=3,
        rate=0.5,
    )
    np.testing.assert_allclose(result["train_mse"], [16.0, 4.0, 1.0, 0.25])
    np.testing.assert_allclose(result["validation_mse"], [4.0, 0.0, 1.0, 2.25])
    assert result["selected_step"] == 1
    np.testing.assert_allclose(result["query_predictions"], [2.0, 6.0])


@pytest.mark.parametrize(
    ("x", "y"),
    [
        (np.array([]), np.array([], dtype=int)),
        (np.array([1.0, np.nan]), np.array([0, 1])),
        (np.array([1.0, 2.0]), np.array([0])),
    ],
)
def test_invalid_split_input_rejected(x: Any, y: Any) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(best_gini_split, x, y)
