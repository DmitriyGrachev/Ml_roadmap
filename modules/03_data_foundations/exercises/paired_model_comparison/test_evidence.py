"""Saved claims are checked against actual snapshot, predictions, and draws."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from .evidence import validate_evidence


def _save(root: Path, filename: str, value: object) -> str:
    data = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    (root / filename).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _fixture(root: Path) -> dict[str, object]:
    snapshot = [
        {"row_id": "r1", "unit_id": "u1", "label": 10.0},
        {"row_id": "r2", "unit_id": "u1", "label": 10.0},
        {"row_id": "r3", "unit_id": "u2", "label": 10.0},
        {"row_id": "r4", "unit_id": "u3", "label": 10.0},
    ]
    predictions = [
        {"row_id": "r1", "prediction_a": 9.0, "prediction_b": 8.0, "loss_a": 1.0, "loss_b": 2.0},
        {"row_id": "r2", "prediction_a": 7.0, "prediction_b": 5.0, "loss_a": 3.0, "loss_b": 5.0},
        {"row_id": "r3", "prediction_a": 8.0, "prediction_b": 9.0, "loss_a": 2.0, "loss_b": 1.0},
        {"row_id": "r4", "prediction_a": 6.0, "prediction_b": 6.0, "loss_a": 4.0, "loss_b": 4.0},
    ]
    seed = 3
    indices = np.random.default_rng(seed).integers(0, 3, size=(120, 3)).tolist()
    per_unit = np.asarray([1.5, -1.0, 0.0], dtype=np.float64)
    draws = per_unit[np.asarray(indices)].mean(axis=1)
    lower, upper = np.quantile(draws, [0.05, 0.95])
    manifest: dict[str, object] = {
        "schema_version": 1,
        "exercise_id": "data-paired-model-comparison",
        "dataset_sha256": _save(root, "snapshot.json", snapshot),
        "split_sha256": _save(root, "split.json", {"evaluation_row_ids": ["r1", "r2", "r3", "r4"]}),
        "config": {
            "seed": seed,
            "n_resamples": 120,
            "confidence": 0.9,
            "loss": "absolute_error",
            "unit_policy": "cluster_by_unit_id",
        },
        "predictions_sha256": _save(root, "predictions.json", predictions),
        "resamples_sha256": _save(
            root, "resamples.json", {"unit_ids": ["u1", "u2", "u3"], "indices": indices}
        ),
        "effect": 1 / 6,
        "lower": float(lower),
        "upper": float(upper),
        "unit_count": 3,
        "resample_count": 120,
    }
    _save(root, "manifest.json", manifest)
    return manifest


def test_valid_saved_evidence_replays_without_student_function(tmp_path: Path) -> None:
    _fixture(tmp_path)
    validate_evidence(tmp_path)


def test_swapped_prediction_bytes_even_with_updated_hash_are_rejected(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    rows = json.loads((tmp_path / "predictions.json").read_text(encoding="utf-8"))
    rows[0]["prediction_a"], rows[0]["prediction_b"] = (
        rows[0]["prediction_b"],
        rows[0]["prediction_a"],
    )
    manifest["predictions_sha256"] = _save(tmp_path, "predictions.json", rows)
    _save(tmp_path, "manifest.json", manifest)
    with pytest.raises(ValueError, match="loss"):
        validate_evidence(tmp_path)


def test_wrong_unit_ids_rejected_even_with_updated_hash(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    draws = json.loads((tmp_path / "resamples.json").read_text(encoding="utf-8"))
    draws["unit_ids"] = ["u1", "u2", "wrong"]
    manifest["resamples_sha256"] = _save(tmp_path, "resamples.json", draws)
    _save(tmp_path, "manifest.json", manifest)
    with pytest.raises(ValueError, match="unit"):
        validate_evidence(tmp_path)


def test_stale_snapshot_bytes_rejected(tmp_path: Path) -> None:
    _fixture(tmp_path)
    snapshot = json.loads((tmp_path / "snapshot.json").read_text(encoding="utf-8"))
    snapshot[0]["label"] = 9.0
    _save(tmp_path, "snapshot.json", snapshot)
    with pytest.raises(ValueError, match="saved bytes"):
        validate_evidence(tmp_path)


def test_changed_metric_rejected(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    config = manifest["config"]
    assert isinstance(config, dict)
    config["loss"] = "squared_error"
    _save(tmp_path, "manifest.json", manifest)
    with pytest.raises(ValueError, match="loss"):
        validate_evidence(tmp_path)


def test_reported_effect_and_interval_replayed(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    manifest["effect"] = 0.0
    _save(tmp_path, "manifest.json", manifest)
    with pytest.raises(ValueError, match="effect"):
        validate_evidence(tmp_path)
    manifest["effect"] = 1 / 6
    manifest["upper"] = 99.0
    _save(tmp_path, "manifest.json", manifest)
    with pytest.raises(ValueError, match="interval"):
        validate_evidence(tmp_path)
