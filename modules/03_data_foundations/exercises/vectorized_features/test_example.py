"""Fixed author arithmetic must not stand in for learner implementation."""

import numpy as np

from .example import run_example


def test_fixed_masked_reduction_and_similarity_arithmetic() -> None:
    result = run_example()
    np.testing.assert_array_equal(result["count"], [2, 1, 0])
    np.testing.assert_allclose(result["mean"], [4, 8, 0])
    np.testing.assert_allclose(result["scale"], [2, 1, 1])
    np.testing.assert_allclose(result["standardized"], [[-1, 0, 0], [1, 0, 0]])
    np.testing.assert_allclose(result["similarities"], [[1, 0, 0], [0, 0, 0]])
