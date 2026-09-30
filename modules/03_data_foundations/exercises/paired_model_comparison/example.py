"""Small completed illustration using sensor measurements, not learner models."""

import numpy as np


def run_example() -> dict[str, float | int]:
    # Two sensors, three aligned measurements. Sensor S1 appears twice.
    label = np.asarray([10.0, 12.0, 8.0], dtype=np.float64)
    reading_a = np.asarray([8.0, 12.0, 4.0], dtype=np.float64)
    reading_b = np.asarray([9.0, 10.0, 6.0], dtype=np.float64)
    row_differences = np.abs(label - reading_b) - np.abs(label - reading_a)
    per_sensor = np.asarray([np.mean(row_differences[:2]), row_differences[2]], dtype=np.float64)
    samples = np.random.default_rng(17).integers(0, 2, size=(200, 2))
    interval = np.quantile(per_sensor[samples].mean(axis=1), [0.05, 0.95])
    return {
        "effect": float(per_sensor.mean()),
        "lower": float(interval[0]),
        "upper": float(interval[1]),
        "unit_count": 2,
        "resample_count": 200,
    }


if __name__ == "__main__":
    print(run_example())
