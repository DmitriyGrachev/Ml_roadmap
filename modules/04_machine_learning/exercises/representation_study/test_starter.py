"""Hand-derived inverse projections catch transposes, lost means and mutation."""

import numpy as np
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import reconstruct_from_components

pytestmark = pytest.mark.student_exercise


def test_inverse_projection_keeps_mean_and_uses_component_rows() -> None:
    scores = np.array([[2.0, 3.0], [-1.0, 4.0]])
    components = np.array([[1.0, 0.0, 0.0], [0.0, 0.6, 0.8]])
    mean = np.array([10.0, 20.0, 30.0])
    snapshots = [a.copy() for a in (scores, components, mean)]
    result = exercise_call(reconstruct_from_components, scores, components, mean)
    np.testing.assert_allclose(result, [[12.0, 21.8, 32.4], [9.0, 22.4, 33.2]])
    assert result.shape == (2, 3)
    assert result.dtype == np.float64
    assert np.isfinite(result).all()
    for array, before in zip((scores, components, mean), snapshots, strict=True):
        np.testing.assert_array_equal(array, before)
        assert not np.shares_memory(result, array)


def test_one_component_preserves_all_rows_without_requiring_orthonormality() -> None:
    result = exercise_call(
        reconstruct_from_components,
        np.array([[-2.0], [0.0], [2.0]]),
        np.array([[1.0, 2.0]]),
        np.array([10.0, 5.0]),
    )
    np.testing.assert_array_equal(result, [[8.0, 1.0], [10.0, 5.0], [12.0, 9.0]])


@pytest.mark.parametrize(
    ("scores", "components", "mean"),
    [
        (np.ones(2), np.ones((2, 3)), np.ones(3)),
        (np.ones((2, 1)), np.ones(3), np.ones(3)),
        (np.ones((2, 1)), np.ones((2, 3)), np.ones(3)),
        (np.ones((2, 1)), np.ones((1, 3)), np.ones((1, 3))),
        (np.ones((2, 1)), np.ones((1, 3)), np.ones(2)),
        (np.empty((0, 1)), np.ones((1, 3)), np.ones(3)),
        (np.ones((2, 0)), np.empty((0, 3)), np.ones(3)),
        (np.ones((2, 1)), np.empty((1, 0)), np.empty(0)),
        (np.array([[np.nan]]), np.ones((1, 3)), np.ones(3)),
        (np.ones((1, 1)), np.array([[np.inf]]), np.ones(1)),
        (np.ones((1, 1)), np.ones((1, 1)), np.array([np.nan])),
    ],
)
def test_invalid_coordinates_rejected(
    scores: np.ndarray, components: np.ndarray, mean: np.ndarray
) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(reconstruct_from_components, scores, components, mean)
