"""Regression errors can differ substantially across cycling routes."""

import numpy as np
from sklearn.metrics import mean_absolute_error, root_mean_squared_error


def route_errors() -> dict[str, float]:
    actual = np.array([10.0, 12.0, 20.0, 24.0])
    predicted = np.array([11.0, 11.0, 22.0, 34.0])
    return {
        "overall_mae_minutes": float(mean_absolute_error(actual, predicted)),
        "overall_rmse_minutes": float(root_mean_squared_error(actual, predicted)),
        "flat_mae_minutes": float(mean_absolute_error(actual[:2], predicted[:2])),
        "hill_mae_minutes": float(mean_absolute_error(actual[2:], predicted[2:])),
    }


def main() -> None:
    print(route_errors())


if __name__ == "__main__":
    main()
