"""Catch unweighted split scores, missing candidate thresholds, and test tuning."""

import numpy as np
from sklearn.tree import DecisionTreeRegressor

from .demo import residual_curve, sse_candidates


def test_thresholds_and_weighted_sse_match_hand_and_sklearn() -> None:
    x = np.array([0.0, 1.0, 3.0, 4.0])
    y = np.array([0.0, 0.0, 4.0, 4.0])
    candidates = sse_candidates(x, y)
    np.testing.assert_allclose(candidates, [[0.5, 32 / 3], [2.0, 0.0], [3.5, 32 / 3]])
    tree = DecisionTreeRegressor(max_depth=1, random_state=0).fit(x[:, None], y)
    assert tree.tree_.threshold[0] == candidates[np.argmin(candidates[:, 1]), 0]


def test_three_residual_steps_reduce_train_error_and_select_only_validation() -> None:
    result = residual_curve(
        np.array([0.0, 1.0, 2.0, 3.0]),
        np.array([0.0, 0.0, 4.0, 4.0]),
        np.array([0.2, 2.8]),
        np.array([0.0, 4.0]),
        steps=3,
        rate=0.5,
    )
    np.testing.assert_allclose(result["train_mse"], [4.0, 1.0, 0.25, 0.0625])
    np.testing.assert_allclose(result["validation_mse"], [4.0, 1.0, 0.25, 0.0625])
    assert result["selected_step"] == 3
    np.testing.assert_allclose(result["validation_predictions"], [0.25, 3.75])


def test_validation_may_prefer_step_zero_and_predictions_follow_selection() -> None:
    result = residual_curve(
        np.array([0.0, 1.0, 2.0, 3.0]),
        np.array([0.0, 0.0, 4.0, 4.0]),
        np.array([0.2, 2.8]),
        np.array([2.0, 2.0]),
        steps=3,
        rate=0.5,
    )
    assert result["selected_step"] == 0
    np.testing.assert_array_equal(result["validation_predictions"], [2.0, 2.0])
    assert result["train_mse"][-1] < result["train_mse"][0]
