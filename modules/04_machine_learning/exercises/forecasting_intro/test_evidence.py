"""Evidence arithmetic and chronology, not a completed forecasting study."""

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


def test_missing_artifacts_fail(tmp_path: Path) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    with pytest.raises(ValueError, match="invalid JSON"):
        module.validate_evidence(tmp_path)


def test_mae_uses_saved_predictions() -> None:
    module = importlib.import_module(__package__ + ".evidence")
    assert module.mae([10, 20], [8, 24]) == 3.0
    for predicted in ([8], [True, 24], [float("nan"), 24]):
        with pytest.raises(ValueError, match=r"prediction count|finite numeric"):
            module.mae([10, 20], predicted)


@pytest.mark.parametrize("predictions", [None, 2, "12", {}])
def test_prediction_shape_errors_are_explicit(predictions: Any) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    with pytest.raises(ValueError, match="prediction list"):
        module.mae([1.0], predictions)


@pytest.mark.parametrize(
    "dates",
    [["2024-01-01", "2024-01-03"], ["2024-01-02", "2024-01-01"], ["2024-01-01", "2024-01-01"]],
)
def test_missing_reordered_duplicate_days_are_rejected(dates: list[str]) -> None:
    module = importlib.import_module(__package__ + ".fixture")
    import pandas as pd

    with pytest.raises(ValueError, match="daily"):
        module.validate_series(pd.Series([1, 2], index=pd.to_datetime(dates)))


def test_example_is_a_different_tiny_calendar_task() -> None:
    module = importlib.import_module(__package__ + ".example")
    assert module.previous_day_error() == 3.0


def forecast_bundle(root: Path) -> dict[str, Any]:
    """Infrastructure fixture: dummy zero model predictions, never a fitted study."""
    fixture = importlib.import_module(__package__ + ".fixture")
    rows = json.loads(fixture.dataset_bytes())
    dates = [row["date"] for row in rows]
    values = [float(row["count"]) for row in rows]
    test = dates[-2:]
    split = {
        "train_origins": dates[7:-2],
        "test_origins": test,
        "random_train_origins": dates[8:],
        "random_test_origins": dates[7:8],
    }
    (root / "data.json").write_bytes(fixture.dataset_bytes())
    (root / "split.json").write_text(json.dumps(split))
    identity = {
        "run_id": "test-only",
        "dataset_sha256": hashlib.sha256(fixture.dataset_bytes()).hexdigest(),
        "split_sha256": hashlib.sha256((root / "split.json").read_bytes()).hexdigest(),
    }
    predictions = {"naive": values[-3:-1], "seasonal": values[-9:-7], "model": [0.0, 0.0]}
    # Last counts: 38, 39; preceding: 29, 38; weekly lags: 37, 38.
    output = {
        **identity,
        "origins": test,
        "fit_origins": {day: dates[7:-2] for day in test},
        "predictions": predictions,
        "mae": {"naive": 5.0, "seasonal": 1.0, "model": 38.5},
        "random": {"origins": dates[7:8], "predictions": [0.0]},
        "comparison": {"random_mae": 21.0, "temporal_mae": 38.5},
    }
    (root / "outputs.json").write_text(json.dumps(output))
    (root / "implementation.txt").write_text("TEST ONLY: dummy predictions; no fit")
    (root / "report.md").write_text("TEST ONLY: arithmetic/identity fixture")
    manifest = {
        **identity,
        "schema_version": 1,
        "exercise_id": "ml-forecasting-intro",
        "config": {"horizon": 1, "model_family": "Ridge"},
        "review_status": "REQUIRES_REVIEW",
        "artifacts": {},
    }
    refresh_bundle(root, manifest)
    return manifest


def refresh_bundle(root: Path, manifest: dict[str, Any]) -> None:
    for path in root.iterdir():
        if path.name != "manifest.json":
            manifest["artifacts"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (root / "manifest.json").write_text(json.dumps(manifest))


@pytest.mark.parametrize(
    "change",
    [
        None,
        "prediction",
        "score",
        "identity",
        "origin",
        "future_fit",
        "horizon",
        "random_score",
        "bytes",
        "dataset",
        "split",
    ],
)
def test_saved_forecast_bundle_rejects_tampering(tmp_path: Path, change: str | None) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    manifest = forecast_bundle(tmp_path)
    output = json.loads((tmp_path / "outputs.json").read_text())
    if change == "prediction":
        output["predictions"]["model"][0] = 10.0
    elif change == "score":
        output["mae"]["model"] = 1.0
    elif change == "identity":
        output["run_id"] = "foreign"
    elif change == "origin":
        output["origins"].reverse()
    elif change == "future_fit":
        day = output["origins"][0]
        output["fit_origins"][day].append(day)
    elif change == "horizon":
        manifest["config"]["horizon"] = 2
    elif change == "random_score":
        output["comparison"]["random_mae"] = 999
    elif change == "dataset":
        (tmp_path / "data.json").write_text("[]")
    elif change == "split":
        (tmp_path / "split.json").write_text("{}")
    (tmp_path / "outputs.json").write_text(json.dumps(output))
    refresh_bundle(tmp_path, manifest)
    if change == "bytes":
        (tmp_path / "report.md").write_text("changed bytes")
    if change is None:
        module.validate_evidence(tmp_path)
    else:
        with pytest.raises(ValueError, match=r"differ|precede|one-day|stale|does not match"):
            module.validate_evidence(tmp_path)


@pytest.mark.parametrize(("prediction", "score"), [(21.0, 0.0), (59.5, 38.5), (100.0, 79.0)])
def test_random_temporal_comparison_has_no_forced_winner(
    tmp_path: Path, prediction: float, score: float
) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    manifest = forecast_bundle(tmp_path)
    output = json.loads((tmp_path / "outputs.json").read_text())
    output["random"]["predictions"] = [prediction]
    output["comparison"]["random_mae"] = score
    (tmp_path / "outputs.json").write_text(json.dumps(output))
    refresh_bundle(tmp_path, manifest)
    module.validate_evidence(tmp_path)
