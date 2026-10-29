"""Fixed rank-deficient design and a hand-computable PCA example."""

from typing import Any

import numpy as np


def geometry_example() -> dict[str, Any]:
    x = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
    y = np.array([2.0, 4.0, 6.0])
    rank = int(np.linalg.matrix_rank(x))
    condition = float("inf") if rank < x.shape[1] else float(np.linalg.cond(x))
    weights = np.linalg.solve(x.T @ x + np.eye(2), x.T @ y)
    return {"rank": rank, "condition": condition, "ridge_weights": weights}


def pca_example() -> dict[str, Any]:
    # These centered rows have sample covariance [[2, 1], [1, 2]].
    points = np.sqrt(2) * np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, -1.0]])
    centered = points - points.mean(axis=0)
    covariance = centered.T @ centered / (len(points) - 1)
    values, vectors = np.linalg.eigh(covariance)
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    return {
        "points": points,
        "covariance": covariance,
        "eigenvalues": values,
        "component": vectors[:, :1],
        "explained_ratio": values / values.sum(),
    }


def main() -> None:
    print("Duplicate columns:", geometry_example())
    print("PCA:", pca_example())
    for epsilon in (0.1, 0.001, 0.00001):
        x = np.array([[1.0, 1.0], [1.0, 1.0 + epsilon]])
        print(
            "epsilon",
            epsilon,
            "condition(X)",
            np.linalg.cond(x),
            "condition(X.T X)",
            np.linalg.cond(x.T @ x),
        )


if __name__ == "__main__":
    main()
