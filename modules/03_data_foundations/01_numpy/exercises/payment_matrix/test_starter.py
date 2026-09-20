"""Acceptance tests for the payment-matrix student boundary."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from roadmap_tools import exercise_call

from .starter import convert_amount_matrix

STARTER_PATH = Path(__file__).with_name("starter.py")


def test_converts_a_float64_matrix_with_broadcasting_without_mutating_inputs() -> None:
    amounts = np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float64)
    rates = np.array([1.1, 0.5], dtype=np.float64)
    original_amounts = amounts.copy()
    original_rates = rates.copy()

    converted = exercise_call(convert_amount_matrix, amounts, rates)

    np.testing.assert_allclose(converted, np.array([[11.0, 10.0], [33.0, 20.0]]))
    assert converted.shape == (2, 2)
    assert converted.dtype == np.float64
    np.testing.assert_array_equal(amounts, original_amounts)
    np.testing.assert_array_equal(rates, original_rates)


def test_preserves_an_empty_row_dimension() -> None:
    amounts = np.empty((0, 2), dtype=np.float64)
    rates = np.array([1.1, 0.5], dtype=np.float64)

    converted = exercise_call(convert_amount_matrix, amounts, rates)

    assert converted.shape == (0, 2)
    assert converted.dtype == np.float64


@pytest.mark.parametrize(
    ("amounts", "rates", "message"),
    [
        (np.ones((2, 2), dtype=np.float64), np.ones(3, dtype=np.float64), "currency"),
        (np.ones(2, dtype=np.float64), np.ones(2, dtype=np.float64), "two-dimensional"),
        (np.ones((2, 2), dtype=np.float64), np.ones((1, 2), dtype=np.float64), "one-dimensional"),
    ],
)
def test_rejects_invalid_matrix_or_rate_shapes(
    amounts: NDArray[np.float64], rates: NDArray[np.float64], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        convert_amount_matrix(amounts, rates)


def test_student_function_contains_no_explicit_loop() -> None:
    assert STARTER_PATH.is_file(), f"missing student starter: {STARTER_PATH}"
    tree = ast.parse(STARTER_PATH.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "convert_amount_matrix"
    )

    assert not any(
        isinstance(node, (ast.For, ast.While, ast.AsyncFor)) for node in ast.walk(function)
    )
