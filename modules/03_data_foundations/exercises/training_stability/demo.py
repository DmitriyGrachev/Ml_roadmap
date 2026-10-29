"""Development-only retraining and a separate fixed-prediction bootstrap."""

from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def retraining_sweep(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    *,
    holdout_ids: NDArray[np.int64],
    seeds: tuple[int, ...],
    sizes: tuple[int, ...],
) -> list[dict[str, Any]]:
    """IID rows only. Holdout values/labels are never accessed for model selection."""
    if (
        holdout_ids.ndim != 1
        or len(holdout_ids) == 0
        or not np.issubdtype(holdout_ids.dtype, np.integer)
        or len(np.unique(holdout_ids)) != len(holdout_ids)
        or np.any(holdout_ids < 0)
        or np.any(holdout_ids >= len(y))
    ):
        raise ValueError("holdout ids must be unique valid row indices")
    development = np.setdiff1d(np.arange(len(y)), holdout_ids)
    validation_size = max(2, len(development) // 4)
    if any(size < 2 or size > len(development) - validation_size for size in sizes):
        raise ValueError("size must leave a separate validation partition")
    rows = []
    for seed in seeds:
        order = np.random.default_rng(seed).permutation(development)
        validation_ids = order[:validation_size]
        pool = order[validation_size:]
        for size in sizes:
            train_ids = pool[:size]
            model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
            model.fit(x[train_ids], y[train_ids])
            prediction = model.predict(x[validation_ids])
            rows.append(
                {
                    "seed": seed,
                    "size": size,
                    "train_ids": train_ids.copy(),
                    "validation_ids": validation_ids.copy(),
                    "mse": float(np.mean((y[validation_ids] - prediction) ** 2)),
                }
            )
    return rows


def paired_bootstrap(
    baseline_losses: NDArray[np.float64],
    candidate_losses: NDArray[np.float64],
    *,
    seed: int,
    repeats: int = 2000,
) -> NDArray[np.float64]:
    """Percentile 95% interval of mean baseline-minus-candidate loss, IID rows."""
    if (
        baseline_losses.ndim != 1
        or len(baseline_losses) == 0
        or candidate_losses.shape != baseline_losses.shape
        or repeats < 2
        or not np.all(np.isfinite(baseline_losses))
        or not np.all(np.isfinite(candidate_losses))
    ):
        raise ValueError("aligned finite loss vectors and repeats >= 2 required")
    differences = baseline_losses - candidate_losses
    indices = np.random.default_rng(seed).integers(0, len(differences), (repeats, len(differences)))
    return np.quantile(differences[indices].mean(axis=1), [0.025, 0.975])


def main() -> None:
    x = np.arange(80, dtype=float)[:, None]
    y = np.sin(x[:, 0] / 4) + 0.05 * x[:, 0]
    rows = retraining_sweep(x, y, holdout_ids=np.arange(65, 80), seeds=(2, 7, 19), sizes=(15, 35))
    for row in rows:
        print("seed", row["seed"], "size", row["size"], "validation MSE", row["mse"])
    print(
        "Conditional paired interval:",
        paired_bootstrap(np.array([1.0, 4.0, 2.0, 9.0]), np.array([0.8, 3.0, 2.5, 7.0]), seed=11),
    )
    print("Locked holdout 65..79: not evaluated during development.")


if __name__ == "__main__":
    main()
