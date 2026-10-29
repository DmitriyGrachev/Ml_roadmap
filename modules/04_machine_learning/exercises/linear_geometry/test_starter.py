"""Catch unpenalized intercept mistakes and covariance convention errors."""

from typing import Any

import numpy as np
import pytest
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

from roadmap_tools.exercise import exercise_call

from .starter import centered_ridge, principal_components

pytestmark = pytest.mark.student_exercise


def test_centered_ridge_matches_library_on_duplicate_nonzero_mean_columns() -> None:
    x = np.array([[10.0, 20.0], [11.0, 22.0], [13.0, 26.0], [14.0, 28.0]])
    y = np.array([3.0, 4.0, 7.0, 9.0])
    w, b = exercise_call(centered_ridge, x, y, 2.0)
    model = Ridge(alpha=2.0).fit(x, y)
    np.testing.assert_allclose(w, model.coef_, atol=1e-10)
    assert b == pytest.approx(model.intercept_)
    np.testing.assert_allclose(x @ w + b, model.predict(x))


def test_constant_target_is_intercept_only_even_with_large_regularization() -> None:
    w, b = exercise_call(
        centered_ridge, np.array([[1.0, 2.0], [4.0, 8.0]]), np.array([7.0, 7.0]), 1000.0
    )
    np.testing.assert_allclose(w, [0.0, 0.0], atol=1e-12)
    assert b == pytest.approx(7.0)


def test_pca_centering_sample_covariance_and_sign_invariant_subspace() -> None:
    x = np.array([[8.0, 2.0], [10.0, 4.0], [12.0, 2.0], [10.0, 0.0]])
    mean, basis, values = exercise_call(principal_components, x, 1)
    np.testing.assert_allclose(mean, [10.0, 2.0])
    np.testing.assert_allclose(values, [8 / 3])
    assert basis.shape == (1, 2)
    np.testing.assert_allclose(basis @ basis.T, [[1.0]])
    # Equal eigenvalues here permit any top direction: compare reconstruction variance.
    centered = x - mean
    assert np.sum((centered @ basis.T) ** 2) / (len(x) - 1) == pytest.approx(values[0])


def test_pca_agrees_with_library_for_distinct_eigenvalues() -> None:
    x = np.array([[5.0, 1.0], [7.0, 1.0], [9.0, 2.0], [11.0, 4.0]])
    mean, basis, values = exercise_call(principal_components, x, 1)
    model = PCA(n_components=1).fit(x)
    np.testing.assert_allclose(mean, model.mean_)
    np.testing.assert_allclose(values, model.explained_variance_)
    np.testing.assert_allclose(basis.T @ basis, model.components_.T @ model.components_)


def test_pca_retains_two_ordered_components_in_three_features() -> None:
    # Orthogonal centered columns have sample variances 12, 16/3 and 4/3.
    # Rotate the first and third features so the retained plane is not coordinate-aligned.
    centered = np.array([[3.0, 2.0, 1.0], [3.0, -2.0, -1.0], [-3.0, 2.0, -1.0], [-3.0, -2.0, 1.0]])
    rotation = np.array([[0.6, 0.0, 0.8], [0.0, 1.0, 0.0], [-0.8, 0.0, 0.6]])
    x = centered @ rotation + np.array([10.0, -4.0, 7.0])
    mean, basis, values = exercise_call(principal_components, x, 2)
    np.testing.assert_allclose(mean, [10.0, -4.0, 7.0])
    assert basis.shape == (2, 3)
    np.testing.assert_allclose(values, [12.0, 16 / 3])
    np.testing.assert_allclose(basis @ basis.T, np.eye(2), atol=1e-12)
    expected_basis = rotation[:2]
    np.testing.assert_allclose(basis.T @ basis, expected_basis.T @ expected_basis, atol=1e-12)
    # The projector alone would miss eigenvectors swapped relative to eigenvalues.
    np.testing.assert_allclose(np.var((x - mean) @ basis.T, axis=0, ddof=1), values, atol=1e-12)


@pytest.mark.parametrize("alpha", [0.0, -1.0, float("nan")])
def test_nonpositive_or_invalid_regularizer_rejected(alpha: Any) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(centered_ridge, np.ones((3, 2)), np.ones(3), alpha)


@pytest.mark.parametrize(
    ("x", "k"),
    [
        (np.ones((1, 2)), 1),
        (np.ones((3, 2)), 0),
        (np.ones((3, 2)), 3),
        (np.array([[np.nan], [2.0]]), 1),
    ],
)
def test_invalid_pca_input_rejected(x: Any, k: Any) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(principal_components, x, k)
