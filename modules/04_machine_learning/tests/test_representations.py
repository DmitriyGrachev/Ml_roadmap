"""Teacher boundaries: a held-out sensor must never become fitted state."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest


def demo() -> ModuleType:
    path = Path(__file__).parents[1] / "04_models/representations.py"
    assert path.is_file(), "Representation teacher demo is not implemented"
    return importlib.import_module("modules.04_machine_learning.04_models.representations")


def test_all_learned_state_uses_train_only(monkeypatch: pytest.MonkeyPatch) -> None:
    api = demo()
    train = np.array([[10.0, 100.0], [20.0, 200.0], [30.0, 300.0], [40.0, 400.0]])
    expected_scaled = np.array([[-3.0, -3.0], [-1.0, -1.0], [1.0, 1.0], [3.0, 3.0]])
    expected_scaled /= np.sqrt(5)
    fitted: list[str] = []
    for name in ("StandardScaler", "PCA", "KMeans", "IsolationForest"):
        cls = getattr(api, name)
        original = cls.fit

        def record(
            self: Any,
            x: np.ndarray,
            *args: Any,
            _name: str = name,
            _fit: Any = original,
            **kwargs: Any,
        ) -> Any:
            np.testing.assert_allclose(x, train if _name == "StandardScaler" else expected_scaled)
            fitted.append(_name)
            return _fit(self, x, *args, **kwargs)

        monkeypatch.setattr(cls, "fit", record)
    model = api.fit_representations(train)
    assert set(fitted) == {"StandardScaler", "PCA", "KMeans", "IsolationForest"}
    count = len(fitted)
    model.inspect(np.array([[10000.0, -10000.0]]))
    assert len(fitted) == count
    np.testing.assert_allclose(model.scaler.mean_, [25.0, 250.0])


def test_inspection_shapes_finite_values_and_input_preservation() -> None:
    api = demo()
    train, queries = api.sensor_data(seed=17)
    before_train, before_queries = train.copy(), queries.copy()
    model = api.fit_representations(train)
    result = model.inspect(queries)
    assert result.projection.shape == (3, 1)
    assert result.cluster.shape == result.anomaly_score.shape == result.anomaly.shape == (3,)
    assert np.isfinite(result.projection).all()
    assert np.isfinite(result.anomaly_score).all()
    assert set(result.anomaly) <= {-1, 1}
    assert len(np.unique(model.inspect(train).cluster)) == 2
    np.testing.assert_array_equal(train, before_train)
    np.testing.assert_array_equal(queries, before_queries)
    repeated = api.fit_representations(train).inspect(queries)
    np.testing.assert_allclose(result.projection, repeated.projection)
    np.testing.assert_allclose(result.anomaly_score, repeated.anomaly_score)
    # Comparing membership relations survives an arbitrary permutation of cluster IDs.
    np.testing.assert_array_equal(
        result.cluster[:, None] == result.cluster,
        repeated.cluster[:, None] == repeated.cluster,
    )


@pytest.mark.parametrize(
    "invalid",
    [
        np.array([1.0, 2.0]),
        np.empty((0, 2)),
        np.ones((1, 2)),
        np.ones((3, 1)),
        np.array([[1.0, np.nan], [2.0, 3.0]]),
        np.array([[1.0, 2.0], [np.inf, 3.0]]),
    ],
)
def test_invalid_training_input_is_rejected(invalid: np.ndarray) -> None:
    with pytest.raises(ValueError, match=r"finite|shape"):
        demo().fit_representations(invalid)


def test_queries_have_same_schema_and_finite_nonempty_rows() -> None:
    api = demo()
    model = api.fit_representations(api.sensor_data()[0])
    for invalid in (np.ones((2, 3)), np.empty((0, 2)), np.array([[np.nan, 2.0]])):
        with pytest.raises(ValueError, match=r"finite|shape"):
            model.inspect(invalid)


def test_distance_table_exposes_the_change_of_units() -> None:
    table = demo().distance_table()
    np.testing.assert_allclose(table[:, 0], [np.sqrt(10004), 18])
    np.testing.assert_allclose(table[:, 1], [np.sqrt(0.832), np.sqrt(2.592)])
    assert np.argmin(table[:, 0]) == 1
    assert np.argmin(table[:, 1]) == 0
