"""Literal masked arithmetic, stable ranking, shape and mutation contracts."""

from typing import Any

import numpy as np
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import masked_standardize, topk_cosine

pytestmark = pytest.mark.student_exercise


def test_authoritative_mask_population_variance_empty_and_constant_columns() -> None:
    values = np.array([[1.0, 7.0, np.nan], [3.0, np.inf, 99.0], [5.0, 7.0, -np.inf]])
    observed = np.array([[True, True, False], [True, False, False], [True, True, False]])
    before = values.copy()
    mask_before = observed.copy()
    z, mean, scale, count = exercise_call(masked_standardize, values, observed)
    np.testing.assert_allclose(mean, [3.0, 7.0, 0.0])
    np.testing.assert_allclose(scale, [np.sqrt(8 / 3), 1.0, 1.0])
    np.testing.assert_array_equal(count, [3, 2, 0])
    np.testing.assert_allclose(z, [[-np.sqrt(1.5), 0, 0], [0, 0, 0], [np.sqrt(1.5), 0, 0]])
    assert z.dtype == mean.dtype == scale.dtype == np.float64
    assert count.dtype == np.int64
    z[0, 0] = 999
    np.testing.assert_array_equal(values, before)
    np.testing.assert_array_equal(observed, mask_before)


def test_noncontiguous_views_reduce_rows_not_columns() -> None:
    base = np.array([[2.0, 99, 10], [6.0, 99, 14]])
    values = base[:, ::2]
    z, mean, scale, count = exercise_call(masked_standardize, values, np.ones_like(values, bool))
    np.testing.assert_allclose(z, [[-1, -1], [1, 1]])
    np.testing.assert_allclose(mean, [4, 12])
    np.testing.assert_allclose(scale, [2, 2])
    np.testing.assert_array_equal(count, [2, 2])
    assert not np.shares_memory(z, base)


@pytest.mark.parametrize(
    ("values", "observed"),
    [
        (np.ones(3), np.ones(3, bool)),
        (np.ones((2, 2)), np.ones((2, 1), bool)),
        (np.ones((2, 2)), np.ones((2, 2), int)),
        (np.array([[np.nan]]), np.array([[True]])),
        (np.array([[np.inf]]), np.array([[True]])),
        (np.empty((0, 2)), np.empty((0, 2), bool)),
        (np.empty((2, 0)), np.empty((2, 0), bool)),
    ],
)
def test_invalid_standardization_input(values: Any, observed: Any) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(masked_standardize, values, observed)


def test_cosine_ties_zero_vectors_and_negative_scores() -> None:
    queries = np.array([[3.0, 0.0], [0.0, 0.0]])
    candidates = np.array([[2.0, 0.0], [0.0, 2.0], [5.0, 0.0], [-1.0, 0.0], [0.0, 0.0]])
    before = (queries.copy(), candidates.copy())
    indices, scores = exercise_call(topk_cosine, queries, candidates, 5)
    np.testing.assert_array_equal(indices, [[0, 2, 1, 4, 3], [0, 1, 2, 3, 4]])
    np.testing.assert_allclose(scores, [[1, 1, 0, 0, -1], [0, 0, 0, 0, 0]])
    assert indices.dtype == np.int64
    assert scores.dtype == np.float64
    np.testing.assert_array_equal(queries, before[0])
    np.testing.assert_array_equal(candidates, before[1])


@pytest.mark.parametrize(("k", "expected"), [(1, [0]), (3, [0, 2, 3])])
def test_cosine_truncated_ties_choose_original_indices(k: int, expected: list[int]) -> None:
    queries = np.array([[1.0, 0.0]])
    candidates = np.array(
        [[1.0, 0.0], [0.0, 1.0], [2.0, 0.0], [3.0, 0.0], [4.0, 0.0], [0.0, -1.0], [5.0, 0.0]]
    )
    indices, scores = exercise_call(topk_cosine, queries, candidates, k)
    np.testing.assert_array_equal(indices, [expected])
    np.testing.assert_allclose(scores, np.ones((1, k)))


def test_cosine_scale_invariance_and_top_one_from_noncontiguous_inputs() -> None:
    queries = np.array([[0.0, 99, 4.0], [1.0, 99, 1.0]])[:, ::2]
    candidates = np.array([[3.0, 99, 0.0], [0.0, 99, 2.0], [2.0, 99, 2.0]])[:, ::2]
    indices, scores = exercise_call(topk_cosine, queries, candidates, 1)
    np.testing.assert_array_equal(indices, [[1], [2]])
    np.testing.assert_allclose(scores, [[1], [1]])
    scaled_indices, scaled_scores = exercise_call(topk_cosine, queries * 7, candidates * 0.25, 1)
    np.testing.assert_array_equal(scaled_indices, indices)
    np.testing.assert_allclose(scaled_scores, scores)


@pytest.mark.parametrize("k", [0, -1, 3, True, 1.5])
def test_invalid_k(k: Any) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(topk_cosine, np.ones((1, 2)), np.ones((2, 2)), k)


@pytest.mark.parametrize(
    ("queries", "candidates"),
    [
        (np.ones(2), np.ones((2, 2))),
        (np.ones((1, 3)), np.ones((2, 2))),
        (np.empty((0, 2)), np.ones((2, 2))),
        (np.ones((1, 2)), np.empty((0, 2))),
        (np.empty((1, 0)), np.empty((2, 0))),
        (np.array([[np.inf]]), np.ones((2, 1))),
        (np.ones((1, 1)), np.array([[np.nan]])),
    ],
)
def test_invalid_cosine_matrices(queries: Any, candidates: Any) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(topk_cosine, queries, candidates, 1)
