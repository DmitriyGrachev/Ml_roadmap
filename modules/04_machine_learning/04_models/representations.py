"""Small offline geometry and sensor inspection demo; no class-quality claim."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

type Matrix = NDArray[np.float64]


def _check(x: Matrix, *, minimum_rows: int) -> None:
    if x.ndim != 2 or x.shape[0] < minimum_rows or x.shape[1] != 2:
        raise ValueError("Expected shape (n, 2) with enough sensor rows")
    if not np.isfinite(x).all():
        raise ValueError("Sensor values must be finite")


@dataclass
class Inspection:
    projection: Matrix
    cluster: NDArray[np.int64]
    anomaly_score: Matrix
    anomaly: NDArray[np.int64]


@dataclass
class Representations:
    scaler: Any
    pca: Any
    clusters: Any
    isolation: Any

    def inspect(self, queries: Matrix) -> Inspection:
        """Apply frozen training state; negative decision scores flag unusual rows."""
        _check(queries, minimum_rows=1)
        scaled = self.scaler.transform(queries)
        return Inspection(
            self.pca.transform(scaled),
            self.clusters.predict(scaled),
            self.isolation.decision_function(scaled),
            self.isolation.predict(scaled),
        )


def fit_representations(train: Matrix, *, seed: int = 17) -> Representations:
    """Learn three separate views of the same standardized training data."""
    _check(train, minimum_rows=2)
    scaler = StandardScaler().fit(train)
    scaled = scaler.transform(train)
    return Representations(
        scaler,
        PCA(n_components=1, svd_solver="full").fit(scaled),
        KMeans(n_clusters=2, n_init=10, random_state=seed).fit(scaled),
        IsolationForest(n_estimators=64, contamination="auto", random_state=seed).fit(scaled),
    )


def distance_table() -> Matrix:
    """Rows A/B, columns raw/scaled Euclidean distance from q=(12 C, 100 rpm)."""
    train = np.array([[10.0, 100.0], [20.0, 200.0], [30.0, 300.0], [40.0, 400.0]])
    scaler = StandardScaler().fit(train)
    candidates = np.array([[10.0, 200.0], [30.0, 100.0]])
    query = np.array([[12.0, 100.0]])
    return np.column_stack(
        (
            np.linalg.norm(candidates - query, axis=1),
            np.linalg.norm(scaler.transform(candidates) - scaler.transform(query), axis=1),
        )
    )


def sensor_data(*, seed: int = 17) -> tuple[Matrix, Matrix]:
    """80 independent synthetic train readings; three later probes, no targets."""
    rng = np.random.default_rng(seed)
    mode = np.repeat([-1.0, 1.0], 40)
    temperature = 24 + 4 * mode + rng.normal(0, 0.8, len(mode))
    speed = 1280 + 80 * mode + rng.normal(0, 20, len(mode))
    train = np.column_stack((temperature, speed))
    queries = np.array([[20.0, 1200.0], [28.0, 1360.0], [45.0, 1900.0]])
    return train, queries


def main() -> None:
    print("distance: candidate raw scaled")
    for name, row in zip(("A", "B"), distance_table(), strict=True):
        print(f"{name} {row[0]:.3f} {row[1]:.3f}")
    train, queries = sensor_data()
    model = fit_representations(train)
    result = model.inspect(queries)
    print(f"train={train.shape} probes={queries.shape}")
    print(f"PCA retained variance={model.pca.explained_variance_ratio_[0]:.3f}")
    print("probe temp_C speed_rpm PC1 same_cluster_as_probe0 decision anomaly")
    for i, row in enumerate(queries):
        same = bool(result.cluster[i] == result.cluster[0])
        print(
            f"{i} {row[0]:.0f} {row[1]:.0f} {result.projection[i, 0]:.3f} "
            f"{same} {result.anomaly_score[i]:.3f} {result.anomaly[i]}"
        )


if __name__ == "__main__":
    main()
