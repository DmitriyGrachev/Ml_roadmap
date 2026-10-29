"""Weighted learner cases differ from the unweighted author derivation."""

from typing import Any

import numpy as np
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import weighted_objective_gradient

pytestmark = pytest.mark.student_exercise


def call(
    kind: Any = "mse", weights: Any = None, l2: Any = 0.5, w: Any = 1.0, b: Any = 0.0, y: Any = None
) -> tuple[float, np.ndarray, float]:
    return exercise_call(
        weighted_objective_gradient,
        np.array([[1.0], [3.0]]),
        np.array([0.0, 2.0]) if y is None else y,
        np.array([w]),
        b,
        np.array([1.0, 3.0]) if weights is None else weights,
        kind=kind,
        l2=l2,
    )


def test_weighted_mse_has_exact_mean_and_no_bias_penalty() -> None:
    loss, dw, db = call()
    assert loss == pytest.approx(1.25)
    np.testing.assert_allclose(dw, [5.5])
    assert db == pytest.approx(2.0)


def test_weight_rescaling_does_not_change_loss_or_gradients() -> None:
    first = call()
    second = call(weights=np.array([7.0, 21.0]))
    assert first[0] == pytest.approx(second[0])
    np.testing.assert_allclose(first[1], second[1])
    assert first[2] == pytest.approx(second[2])


def test_zero_weight_excludes_one_row_from_data_term() -> None:
    loss, dw, db = call(weights=np.array([0.0, 4.0]), l2=0.0)
    assert loss == pytest.approx(1.0)
    np.testing.assert_allclose(dw, [6.0])
    assert db == pytest.approx(2.0)


@pytest.mark.parametrize("kind", ["mse", "bce"])
def test_weighted_gradient_matches_independent_finite_difference(kind: Any) -> None:
    y = np.array([0.0, 1.0])
    loss, dw, db = call(kind=kind, w=0.2, b=-0.3, y=y)
    numeric_w = (
        call(kind=kind, w=0.200001, b=-0.3, y=y)[0] - call(kind=kind, w=0.199999, b=-0.3, y=y)[0]
    ) / 2e-6
    numeric_b = (
        call(kind=kind, w=0.2, b=-0.299999, y=y)[0] - call(kind=kind, w=0.2, b=-0.300001, y=y)[0]
    ) / 2e-6
    assert loss >= 0
    np.testing.assert_allclose(dw, [numeric_w], atol=1e-8)
    assert db == pytest.approx(numeric_b, abs=1e-8)


def test_weighted_bce_extremes_do_not_overflow() -> None:
    loss, dw, db = exercise_call(
        weighted_objective_gradient,
        np.array([[-1000.0], [1000.0]]),
        np.array([1.0, 0.0]),
        np.array([1.0]),
        0.0,
        np.array([1.0, 3.0]),
        kind="bce",
        l2=0.0,
    )
    assert loss == pytest.approx(1000.0)
    np.testing.assert_allclose(dw, [1000.0])
    assert db == pytest.approx(0.5)


@pytest.mark.parametrize(
    "weights",
    [np.array([0.0, 0.0]), np.array([-1.0, 2.0]), np.array([1.0]), np.array([np.nan, 1.0])],
)
def test_invalid_weights_rejected(weights: Any) -> None:
    with pytest.raises(ValueError, match=r"."):
        call(weights=weights)


@pytest.mark.parametrize(
    "kwargs", [{"l2": -1.0}, {"kind": "other"}, {"kind": "bce", "y": np.array([0.0, 2.0])}]
)
def test_invalid_objective_rejected(kwargs: Any) -> None:
    with pytest.raises(ValueError, match=r"."):
        call(**kwargs)


def test_bias_is_not_regularized_even_when_nonzero() -> None:
    loss, dw, db = call(b=2.0)
    assert loss == pytest.approx(9.25)
    np.testing.assert_allclose(dw, [15.5])
    assert db == pytest.approx(6.0)


@pytest.mark.parametrize(
    ("x", "y", "w"),
    [
        (np.ones((2, 1)), np.ones((2, 1)), np.ones(1)),
        (np.ones((2, 1)), np.ones(2), np.ones(2)),
        (np.empty((0, 1)), np.empty(0), np.ones(1)),
        (np.array([[1.0], [np.inf]]), np.ones(2), np.ones(1)),
    ],
)
def test_invalid_shapes_and_nonfinite_features_rejected(x: Any, y: Any, w: Any) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(
            weighted_objective_gradient, x, y, w, 0.0, np.ones(len(y)), kind="mse", l2=0.0
        )


def test_extreme_correct_weighted_bce_does_not_warn_or_clip() -> None:
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        loss, dw, db = exercise_call(
            weighted_objective_gradient,
            np.array([[-1000.0], [1000.0]]),
            np.array([0.0, 1.0]),
            np.array([1.0]),
            0.0,
            np.array([2.0, 1.0]),
            kind="bce",
            l2=0.0,
        )
    assert loss == pytest.approx(0.0)
    np.testing.assert_array_equal(dw, [0.0])
    assert db == 0.0
