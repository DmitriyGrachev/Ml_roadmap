"""Author regression stumps; learner independently builds a Gini splitter."""

from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.tree import DecisionTreeRegressor


def sse_candidates(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float64]:
    values = np.unique(x)
    rows = []
    for threshold in (values[:-1] + values[1:]) / 2:
        left = x <= threshold
        sse = sum(float(np.sum((part - part.mean()) ** 2)) for part in (y[left], y[~left]))
        rows.append((threshold, sse))
    return np.asarray(rows, dtype=float).reshape(-1, 2)


def residual_curve(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    validation_x: NDArray[np.float64],
    validation_y: NDArray[np.float64],
    *,
    steps: int = 3,
    rate: float = 0.5,
) -> dict[str, Any]:
    train = np.full(len(y), y.mean())
    valid = np.full(len(validation_y), y.mean())
    train_mse = [float(np.mean((y - train) ** 2))]
    validation_mse = [float(np.mean((validation_y - valid) ** 2))]
    snapshots = [valid.copy()]
    for _ in range(steps):
        stump = DecisionTreeRegressor(max_depth=1, random_state=0).fit(x[:, None], y - train)
        train += rate * stump.predict(x[:, None])
        valid += rate * stump.predict(validation_x[:, None])
        train_mse.append(float(np.mean((y - train) ** 2)))
        validation_mse.append(float(np.mean((validation_y - valid) ** 2)))
        snapshots.append(valid.copy())
    chosen = int(np.argmin(validation_mse))
    return {
        "train_mse": np.asarray(train_mse),
        "validation_mse": np.asarray(validation_mse),
        "selected_step": chosen,
        "validation_predictions": snapshots[chosen],
    }


def main() -> None:
    x = np.array([0.0, 1.0, 3.0, 4.0])
    y = np.array([0.0, 0.0, 4.0, 4.0])
    print("threshold, total within-leaf SSE:", sse_candidates(x, y))
    print("boosting:", residual_curve(x, y, np.array([0.2, 3.8]), np.array([0.0, 4.0])))


if __name__ == "__main__":
    main()
