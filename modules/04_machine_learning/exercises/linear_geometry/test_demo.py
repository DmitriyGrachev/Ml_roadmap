"""Catch false full rank, squared-condition mistakes, and uncentered PCA."""

import numpy as np
import pytest
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

from .demo import geometry_example, pca_example


def test_duplicate_columns_are_nonidentifiable_but_ridge_is_unique() -> None:
    result = geometry_example()
    assert result["rank"] == 1
    assert result["condition"] == float("inf")
    x = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
    expected = Ridge(alpha=1.0, fit_intercept=False).fit(x, np.array([2.0, 4.0, 6.0])).coef_
    np.testing.assert_allclose(result["ridge_weights"], expected)
    np.testing.assert_allclose(result["ridge_weights"], [28 / 29, 28 / 29])


def test_covariance_eigenvalues_and_projection_match_hand_and_library() -> None:
    result = pca_example()
    np.testing.assert_allclose(result["covariance"], [[2.0, 1.0], [1.0, 2.0]])
    np.testing.assert_allclose(result["eigenvalues"], [3.0, 1.0])
    assert result["explained_ratio"][0] == pytest.approx(0.75)
    pca = PCA(n_components=1).fit(result["points"])
    np.testing.assert_allclose(
        result["component"] @ result["component"].T, pca.components_.T @ pca.components_, atol=1e-12
    )
