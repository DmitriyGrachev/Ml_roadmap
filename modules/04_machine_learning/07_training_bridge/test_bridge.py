"""Independent numeric contracts; no model-quality claim."""

from importlib import import_module

import numpy as np
import pytest

from roadmap_tools import exercise_call

PREFIX = "modules.04_machine_learning.07_training_bridge"


def test_neighbor_example_gradient_matches_finite_difference() -> None:
    example = import_module(f"{PREFIX}.example")
    point = 0.7
    epsilon = 1e-6
    difference = (example.loss(point + epsilon) - example.loss(point - epsilon)) / (2 * epsilon)
    assert example.gradient(point) == pytest.approx(difference)
    assert example.loss(example.step(point, 0.05)) < example.loss(point)


@pytest.mark.student_exercise
def test_update_has_independent_expected_values_and_does_not_mutate() -> None:
    starter = import_module(f"{PREFIX}.starter")
    weights = np.array([1.0, -2.0])
    gradient = np.array([4.0, -6.0])
    updated = exercise_call(starter.gradient_step, weights, gradient, 0.25)
    np.testing.assert_allclose(updated, [0.0, -0.5])
    np.testing.assert_array_equal(weights, [1.0, -2.0])
    np.testing.assert_array_equal(gradient, [4.0, -6.0])
    assert not np.shares_memory(updated, weights)
    assert not np.shares_memory(updated, gradient)
    assert updated.dtype == np.float64


@pytest.mark.student_exercise
@pytest.mark.parametrize("rate", [0.0, -0.1, float("nan"), float("inf")])
def test_update_rejects_invalid_rate(rate: float) -> None:
    starter = import_module(f"{PREFIX}.starter")
    with pytest.raises(ValueError, match="rate"):
        exercise_call(starter.gradient_step, np.array([1.0]), np.array([2.0]), rate)


@pytest.mark.student_exercise
@pytest.mark.parametrize(
    ("weights", "gradient"),
    [([1.0, 2.0], [1.0]), ([], []), ([float("nan")], [1.0]), ([1.0], [float("inf")])],
)
def test_update_rejects_invalid_vectors(weights: list[float], gradient: list[float]) -> None:
    starter = import_module(f"{PREFIX}.starter")
    with pytest.raises(ValueError, match=r"weights|gradient|vector"):
        exercise_call(starter.gradient_step, np.array(weights), np.array(gradient), 0.1)


@pytest.mark.student_exercise
def test_update_rejects_a_matrix_even_when_shapes_match() -> None:
    starter = import_module(f"{PREFIX}.starter")
    with pytest.raises(ValueError, match=r"weights|gradient|vector"):
        exercise_call(starter.gradient_step, np.array([[1.0]]), np.array([[2.0]]), 0.1)


@pytest.mark.student_exercise
@pytest.mark.parametrize("dtype", ["float32", "int64"])
@pytest.mark.parametrize("invalid_argument", ["weights", "gradient"])
def test_update_rejects_non_float64_vectors(dtype: str, invalid_argument: str) -> None:
    starter = import_module(f"{PREFIX}.starter")
    weights = np.array([1.0], dtype=dtype if invalid_argument == "weights" else "float64")
    gradient = np.array([2.0], dtype=dtype if invalid_argument == "gradient" else "float64")
    with pytest.raises(ValueError, match=r"weights|gradient|vector"):
        exercise_call(starter.gradient_step, weights, gradient, 0.1)
