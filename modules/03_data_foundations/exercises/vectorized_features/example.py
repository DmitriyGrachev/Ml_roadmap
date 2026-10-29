"""Fixed two-row arithmetic; deliberately not a general learner solution."""

from typing import TypedDict

import numpy as np
import numpy.typing as npt


class ExampleResult(TypedDict):
    """Named arrays with the actual dtypes of the worked arithmetic."""

    count: npt.NDArray[np.int64]
    mean: npt.NDArray[np.float64]
    scale: npt.NDArray[np.float64]
    standardized: npt.NDArray[np.float64]
    similarities: npt.NDArray[np.float64]


def run_example() -> ExampleResult:
    """Demonstrate safe masking before reductions and zero-safe normalization."""
    values = np.array([[2.0, 8.0, np.nan], [6.0, np.inf, -99.0]])
    observed = np.array([[True, True, False], [True, False, False]])
    clean = np.where(observed, values, 0.0)
    count = observed.sum(axis=0)
    mean = clean.sum(axis=0) / np.maximum(count, 1)
    deviations = np.where(observed, clean - mean, 0.0)
    scale = np.sqrt((deviations**2).sum(axis=0) / np.maximum(count, 1))
    scale[scale == 0] = 1.0
    queries = np.array([[1.0, 0.0], [0.0, 0.0]])
    candidates = np.array([[2.0, 0.0], [0.0, 3.0], [0.0, 0.0]])
    products = queries @ candidates.T
    norm_products = (
        np.linalg.norm(queries, axis=1)[:, None] * np.linalg.norm(candidates, axis=1)[None, :]
    )
    similarities = np.divide(
        products, norm_products, out=np.zeros_like(products), where=norm_products != 0
    )
    return {
        "count": count,
        "mean": mean,
        "scale": scale,
        "standardized": deviations / scale,
        "similarities": similarities,
    }


if __name__ == "__main__":
    print(run_example())
