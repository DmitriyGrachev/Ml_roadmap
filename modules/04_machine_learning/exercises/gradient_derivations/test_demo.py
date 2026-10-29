"""Catch wrong reduction, penalized bias, unstable logits, and derivative signs."""

import numpy as np
import pytest
from sklearn.linear_model import Ridge
from sklearn.metrics import log_loss

from .demo import objective_gradient


def test_mse_derivatives_match_finite_differences_and_ridge() -> None:
    x = np.array([[1.0, 2.0], [-2.0, 1.0], [3.0, -1.0]])
    y = np.array([1.0, -1.0, 2.0])
    w = np.array([0.4, -0.2])
    loss, dw, db = objective_gradient(x, y, w, 0.3, kind="mse", l2=0.7)
    theta = np.r_[w, 0.3]
    numeric = []
    for i in range(3):
        plus, minus = theta.copy(), theta.copy()
        plus[i] += 1e-6
        minus[i] -= 1e-6
        numeric.append(
            (
                objective_gradient(x, y, plus[:2], plus[2], kind="mse", l2=0.7)[0]
                - objective_gradient(x, y, minus[:2], minus[2], kind="mse", l2=0.7)[0]
            )
            / 2e-6
        )
    np.testing.assert_allclose(np.r_[dw, db], numeric, atol=1e-8)
    model = Ridge(alpha=len(y) * 0.7 / 2).fit(x, y)
    _, dw, db = objective_gradient(x, y, model.coef_, model.intercept_, kind="mse", l2=0.7)
    np.testing.assert_allclose(np.r_[dw, db], 0, atol=1e-12)
    assert loss > 0


def test_bce_extreme_logits_are_finite_with_correct_gradient() -> None:
    x = np.array([[-1000.0], [1000.0]])
    loss, dw, db = objective_gradient(x, np.array([1.0, 0.0]), np.array([1.0]), 0.0, kind="bce")
    assert loss == pytest.approx(1000.0)
    np.testing.assert_allclose(dw, [1000.0])
    assert db == pytest.approx(0.0)


def test_bce_library_loss_and_numeric_gradient() -> None:
    x = np.array([[-2.0], [1.0], [3.0]])
    y = np.array([0.0, 1.0, 0.0])
    loss, dw, db = objective_gradient(x, y, np.array([0.3]), -0.4, kind="bce", l2=0.2)
    p = 1 / (1 + np.exp(-(x[:, 0] * 0.3 - 0.4)))
    assert loss == pytest.approx(log_loss(y, p) + 0.2 / 2 * 0.3**2)
    for w, b, expected in [(0.3 + 1e-6, -0.4, dw[0]), (0.3, -0.4 + 1e-6, db)]:
        minus_w = 0.3 - 1e-6 if b == -0.4 else 0.3
        minus_b = -0.4 if b == -0.4 else -0.4 - 1e-6
        numeric = (
            objective_gradient(x, y, np.array([w]), b, kind="bce", l2=0.2)[0]
            - objective_gradient(x, y, np.array([minus_w]), minus_b, kind="bce", l2=0.2)[0]
        ) / 2e-6
        assert expected == pytest.approx(numeric, abs=1e-8)


def test_extreme_correct_bce_avoids_overflow_without_clipping() -> None:
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        loss, dw, db = objective_gradient(
            np.array([[-1000.0], [1000.0]]), np.array([0.0, 1.0]), np.array([1.0]), 0.0, kind="bce"
        )
    assert loss == pytest.approx(0.0)
    np.testing.assert_array_equal(dw, [0.0])
    assert db == 0.0
