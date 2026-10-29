"""Unweighted author derivation; learner task adds nonuniform observation weights."""

import numpy as np
from numpy.typing import NDArray


def objective_gradient(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    w: NDArray[np.float64],
    b: float,
    *,
    kind: str = "mse",
    l2: float = 0.0,
) -> tuple[float, NDArray[np.float64], float]:
    """Mean data loss + l2/2 * ||w||², without a bias penalty."""
    z = x @ w + b
    if kind == "mse":
        losses = (z - y) ** 2
        dz = 2 * (z - y)
    elif kind == "bce":
        losses = np.logaddexp(0.0, z) - y * z
        probability = np.exp(-np.logaddexp(0.0, -z))
        dz = probability - y
    else:
        raise ValueError("kind must be mse or bce")
    return (
        float(np.mean(losses) + l2 / 2 * (w @ w)),
        x.T @ dz / len(y) + l2 * w,
        float(np.mean(dz)),
    )


def main() -> None:
    x = np.array([[1.0, 2.0], [-2.0, 1.0], [3.0, -1.0]])
    for kind, y in [("mse", np.array([1.0, -1.0, 2.0])), ("bce", np.array([1.0, 0.0, 1.0]))]:
        loss, dw, db = objective_gradient(x, y, np.array([0.4, -0.2]), 0.3, kind=kind, l2=0.7)
        print(kind, "mean objective:", loss, "dw:", dw, "db:", db)
    print(
        "Extreme wrong predictions:",
        objective_gradient(
            np.array([[-1000.0], [1000.0]]), np.array([1.0, 0.0]), np.array([1.0]), 0.0, kind="bce"
        ),
    )


if __name__ == "__main__":
    main()
