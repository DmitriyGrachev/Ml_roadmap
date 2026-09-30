"""Changing feature units can change the nearest row."""

import numpy as np


def run_example() -> dict[str, tuple[float, float] | int]:
    """Compare direct distances with distances after a known unit conversion."""
    train = np.array([[0.0, 0.0], [3.0, 100.0]])
    query = np.array([2.0, 0.0])
    raw = np.linalg.norm(train - query, axis=1)

    # Convert the second coordinate from centimeters to meters in both arrays.
    converted_train = train.copy()
    converted_query = query.copy()
    converted_train[:, 1] /= 100.0
    converted_query[1] /= 100.0
    converted = np.linalg.norm(converted_train - converted_query, axis=1)
    return {
        "raw_distances": (float(raw[0]), float(raw[1])),
        "converted_distances": (float(converted[0]), float(converted[1])),
        "raw_nearest_row": int(np.argmin(raw)),
        "converted_nearest_row": int(np.argmin(converted)),
    }


if __name__ == "__main__":
    print(run_example())
