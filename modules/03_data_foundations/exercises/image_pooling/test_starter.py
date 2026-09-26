"""Literal block averages expose swapped axes and incorrect reshape order."""

from typing import cast

import numpy as np
import numpy.typing as npt
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import block_means

pytestmark = pytest.mark.student_exercise


def test_rectangular_blocks_average_their_spatial_pixels() -> None:
    image = np.arange(24, dtype=np.float64).reshape(4, 6)
    result = exercise_call(block_means, image, (2, 3))
    np.testing.assert_allclose(result, [[4.0, 7.0], [16.0, 19.0]])
    assert result.dtype == np.float64


def test_noncontiguous_view_and_input_are_unchanged() -> None:
    base = np.arange(24, dtype=np.float64).reshape(4, 6)
    image = base[:, ::2]
    before = base.copy()
    result = exercise_call(block_means, image, (2, 1))
    np.testing.assert_allclose(result, [[3, 5, 7], [15, 17, 19]])
    result[0, 0] = -100
    np.testing.assert_array_equal(base, before)


def test_unit_blocks_return_independent_float_array() -> None:
    image = np.array([[0.25, -1.25]])
    result = exercise_call(block_means, image, (1, 1))
    np.testing.assert_allclose(result, [[0.25, -1.25]])
    assert not np.shares_memory(image, result)


def test_one_block_covers_whole_image() -> None:
    assert exercise_call(block_means, np.array([[1.0, 2.0], [3.0, 8.0]]), (2, 2)).tolist() == [
        [3.5]
    ]


@pytest.mark.parametrize("shape", [(0, 1), (-1, 1), (True, 1), (1.5, 1), (3, 2)])
def test_invalid_or_nondividing_block_shape(shape: tuple[object, object]) -> None:
    with pytest.raises(ValueError, match="block"):
        exercise_call(block_means, np.ones((4, 4)), cast(tuple[int, int], shape))


@pytest.mark.parametrize(
    "image",
    [np.zeros((0, 2)), np.ones(4), np.ones((1, 2, 3)), np.array([[np.nan]]), np.array([[np.inf]])],
)
def test_empty_nonmatrix_and_nonfinite_images(image: npt.NDArray[np.float64]) -> None:
    with pytest.raises(ValueError, match="image"):
        exercise_call(block_means, image, (1, 1))
