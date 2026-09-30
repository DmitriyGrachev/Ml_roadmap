"""Read-only replay of saved paired-comparison evidence."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import numpy as np

from roadmap_tools.experiment_evidence import checked_artifact, validate_identity


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON value: {value}")


def _read_json(path: Path) -> object:
    try:
        return cast(
            object, json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON artifact: {path.name}") from exc


def _object(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be an object")
    return cast(Mapping[str, object], value)


def _array(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return cast(list[object], value)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be nonempty text")
    return value


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be finite numeric data")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite numeric data")
    return number


def _integer(value: object, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer")
    return value


def _same(actual: float, claimed: object, name: str) -> None:
    if not math.isclose(actual, _number(claimed, name), rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError(f"{name} differs from replayed evidence")


def _artifact(root: Path, manifest: Mapping[str, object], name: str, sha_field: str) -> object:
    digest = _text(manifest.get(sha_field), sha_field)
    return _read_json(checked_artifact(root, name, digest))


def validate_evidence(root: Path) -> None:
    """Replay schema-1 local artifacts; raise ValueError for inconsistent claims.

    The manifest names fixed local files. Its digests bind those files to the
    recorded snapshot, but human review still determines whether that snapshot
    was an appropriate held-out evaluation set.
    """
    manifest = _object(_read_json(root / "manifest.json"), "manifest")
    dataset_sha = _text(manifest.get("dataset_sha256"), "dataset_sha256")
    split_sha = _text(manifest.get("split_sha256"), "split_sha256")
    validate_identity(
        manifest,
        exercise_id="data-paired-model-comparison",
        dataset_sha256=dataset_sha,
        split_sha256=split_sha,
    )
    config = _object(manifest.get("config"), "config")
    seed = _integer(config.get("seed"), "seed")
    n_resamples = _integer(config.get("n_resamples"), "n_resamples")
    confidence = _number(config.get("confidence"), "confidence")
    if seed < 0 or n_resamples < 100 or not 0 < confidence < 1:
        raise ValueError("invalid seed, n_resamples, or confidence")
    if config.get("unit_policy") != "cluster_by_unit_id":
        raise ValueError("unit policy must preserve repeated unit IDs")
    loss_name = config.get("loss")
    if not isinstance(loss_name, str) or loss_name not in {"absolute_error", "squared_error"}:
        raise ValueError("unsupported loss")

    snapshot = _array(_artifact(root, manifest, "snapshot.json", "dataset_sha256"), "snapshot")
    split = _object(_artifact(root, manifest, "split.json", "split_sha256"), "split")
    predictions = _array(
        _artifact(root, manifest, "predictions.json", "predictions_sha256"), "predictions"
    )
    resamples = _object(
        _artifact(root, manifest, "resamples.json", "resamples_sha256"), "resamples"
    )

    labels: dict[str, tuple[str, float]] = {}
    for record in snapshot:
        row = _object(record, "snapshot row")
        row_id = _text(row.get("row_id"), "row_id")
        unit_id = _text(row.get("unit_id"), "unit_id")
        if row_id in labels:
            raise ValueError("duplicate snapshot row_id")
        labels[row_id] = (unit_id, _number(row.get("label"), "label"))
    split_ids = [
        _text(value, "split row_id")
        for value in _array(split.get("evaluation_row_ids"), "split IDs")
    ]
    if (
        len(split_ids) != len(set(split_ids))
        or not split_ids
        or any(i not in labels for i in split_ids)
    ):
        raise ValueError("split row IDs must be unique saved snapshot IDs")
    if len(predictions) != len(split_ids):
        raise ValueError("prediction row IDs differ from split IDs")

    differences: dict[str, list[float]] = defaultdict(list)
    for expected_id, record in zip(split_ids, predictions, strict=True):
        row = _object(record, "prediction row")
        if row.get("row_id") != expected_id:
            raise ValueError("prediction row IDs differ from split IDs")
        unit_id, label = labels[expected_id]
        prediction_a = _number(row.get("prediction_a"), "prediction_a")
        prediction_b = _number(row.get("prediction_b"), "prediction_b")
        saved_a = _number(row.get("loss_a"), "loss_a")
        saved_b = _number(row.get("loss_b"), "loss_b")
        error_a = label - prediction_a
        error_b = label - prediction_b
        if loss_name == "absolute_error":
            actual_a, actual_b = abs(error_a), abs(error_b)
        else:
            actual_a, actual_b = error_a**2, error_b**2
        if not math.isfinite(actual_a) or not math.isfinite(actual_b):
            raise ValueError("loss overflowed")
        _same(actual_a, saved_a, "loss_a")
        _same(actual_b, saved_b, "loss_b")
        differences[unit_id].append(actual_b - actual_a)

    unit_ids = sorted(differences)
    if len(unit_ids) < 2:
        raise ValueError("at least two independent units are required")
    if _array(resamples.get("unit_ids"), "unit IDs") != unit_ids:
        raise ValueError("resample unit IDs differ from snapshot units")
    values = np.asarray(
        [np.mean(differences[unit], dtype=np.float64) for unit in unit_ids], dtype=np.float64
    )
    effect = float(np.mean(values, dtype=np.float64))
    if not math.isfinite(effect):
        raise ValueError("effect is nonfinite")

    raw_indices = _array(resamples.get("indices"), "resample indices")
    if len(raw_indices) != n_resamples:
        raise ValueError("resample count differs from config")
    indices: list[list[int]] = []
    for raw_draw in raw_indices:
        draw = _array(raw_draw, "resample draw")
        if len(draw) != len(unit_ids):
            raise ValueError("resample draw must sample whole units")
        indices.append([])
        for index in draw:
            parsed = _integer(index, "resample index")
            if not 0 <= parsed < len(unit_ids):
                raise ValueError("resample index outside unit range")
            indices[-1].append(parsed)
    actual_indices = np.asarray(indices, dtype=np.int64)
    expected_indices = np.random.default_rng(seed).integers(
        0, len(unit_ids), size=(n_resamples, len(unit_ids))
    )
    if not np.array_equal(actual_indices, expected_indices):
        raise ValueError("resample indices differ from seeded unit draws")
    sampled = values[actual_indices].mean(axis=1, dtype=np.float64)
    alpha = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(sampled, [alpha, 1.0 - alpha])
    _same(effect, manifest.get("effect"), "effect")
    _same(float(lower), manifest.get("lower"), "interval lower")
    _same(float(upper), manifest.get("upper"), "interval upper")
    if _integer(manifest.get("unit_count"), "unit_count") != len(unit_ids):
        raise ValueError("unit count differs from replay")
    if _integer(manifest.get("resample_count"), "resample_count") != n_resamples:
        raise ValueError("resample count differs from replay")
