"""Validate a learner's traceable, offline PyTorch experiment report."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _artifact_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else _REPOSITORY_ROOT / path


def _nonempty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    if re.search(r"\b(?:todo|tbd|placeholder|mock|not run)\b", value, re.IGNORECASE):
        raise ValueError(f"{field} contains a placeholder")
    return value


def _ids(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a nonempty list")
    result = [_nonempty_text(item, field) for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{field} contains duplicate IDs")
    return result


def validate_report(path: Path) -> dict[str, Any]:
    """Check schema, data/checkpoint bytes, computed accuracy, and analysis.

    The check establishes traceability of submitted values, not model quality or
    authenticity of the learner's experiment. The checkpoint is never unpickled.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("report must be readable JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("report must be an object")
    required = {
        "schema_version",
        "task",
        "seed",
        "dataset",
        "dataset_sha256",
        "code_revision",
        "config",
        "train_ids",
        "validation_ids",
        "checkpoint",
        "checkpoint_sha256",
        "versions",
        "labels",
        "predictions",
        "metrics",
        "analysis",
    }
    if set(payload) != required:
        raise ValueError("report fields do not match schema version 1")
    if payload["schema_version"] != 1:
        raise ValueError("unsupported schema_version")
    _nonempty_text(payload["task"], "task")
    if (
        isinstance(payload["seed"], bool)
        or not isinstance(payload["seed"], int)
        or payload["seed"] < 0
    ):
        raise ValueError("seed must be a nonnegative integer")
    dataset_text = _nonempty_text(payload["dataset"], "dataset")
    dataset = _artifact_path(dataset_text)
    if not dataset.is_file():
        raise ValueError("dataset snapshot file does not exist")
    dataset_checksum = payload["dataset_sha256"]
    if (
        not isinstance(dataset_checksum, str)
        or re.fullmatch(r"[0-9a-f]{64}", dataset_checksum) is None
    ):
        raise ValueError("dataset_sha256 must be lowercase SHA-256")
    if hashlib.sha256(dataset.read_bytes()).hexdigest() != dataset_checksum:
        raise ValueError("dataset_sha256 does not match dataset bytes")
    code_revision = _nonempty_text(payload["code_revision"], "code_revision")
    if (
        code_revision != "working-tree (dirty)"
        and re.fullmatch(r"[0-9a-f]{40}", code_revision) is None
    ):
        raise ValueError("code_revision must be a Git SHA or working-tree (dirty)")
    config = payload["config"]
    if not isinstance(config, dict) or set(config) != {
        "batch_size",
        "learning_rate",
        "epochs",
        "device",
        "input_dim",
        "n_classes",
        "optimizer",
        "momentum",
    }:
        raise ValueError("config requires training and model dimensions")
    for key in ("batch_size", "epochs", "input_dim", "n_classes"):
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"config {key} must be a positive integer")
    if config["n_classes"] < 2:
        raise ValueError("config n_classes must be at least two")
    learning_rate = config["learning_rate"]
    if (
        isinstance(learning_rate, bool)
        or not isinstance(learning_rate, (int, float))
        or not math.isfinite(learning_rate)
        or learning_rate <= 0
    ):
        raise ValueError("config learning_rate must be finite and positive")
    device = config["device"]
    if not isinstance(device, str) or re.fullmatch(r"cpu|cuda:[0-9]+", device) is None:
        raise ValueError("config device must be cpu or cuda:N")
    if config["optimizer"] != "SGD":
        raise ValueError("config optimizer must be SGD")
    momentum = config["momentum"]
    if (
        isinstance(momentum, bool)
        or not isinstance(momentum, (int, float))
        or not math.isfinite(momentum)
        or not 0 <= momentum < 1
    ):
        raise ValueError("config momentum must be in [0, 1)")
    train_ids = _ids(payload["train_ids"], "train_ids")
    validation_ids = _ids(payload["validation_ids"], "validation_ids")
    if set(train_ids) & set(validation_ids):
        raise ValueError("split IDs overlap")

    checkpoint_text = _nonempty_text(payload["checkpoint"], "checkpoint")
    checkpoint = _artifact_path(checkpoint_text)
    if not checkpoint.is_file():
        raise ValueError("checkpoint file does not exist")
    checksum = payload["checkpoint_sha256"]
    if not isinstance(checksum, str) or re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
        raise ValueError("checkpoint_sha256 must be lowercase SHA-256")
    if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != checksum:
        raise ValueError("checkpoint_sha256 does not match checkpoint bytes")

    versions = payload["versions"]
    if not isinstance(versions, dict) or not {"python", "torch"} <= set(versions):
        raise ValueError("versions must include python and torch")
    for key, version in versions.items():
        _nonempty_text(key, "version name")
        _nonempty_text(version, f"version {key}")

    labels = payload["labels"]
    predictions = payload["predictions"]
    if not isinstance(labels, list) or not isinstance(predictions, list):
        raise ValueError("labels and predictions must be lists")
    if len(labels) != len(validation_ids) or len(predictions) != len(labels):
        raise ValueError("prediction count must equal validation split count")
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in labels + predictions):
        raise ValueError("labels and predictions must be nonnegative class integers")
    if any(value >= config["n_classes"] for value in labels + predictions):
        raise ValueError("labels and predictions must be within configured class IDs")
    metrics = payload["metrics"]
    if not isinstance(metrics, dict) or set(metrics) != {"count", "accuracy"}:
        raise ValueError("metrics require count and accuracy")
    if metrics["count"] != len(labels) or isinstance(metrics["count"], bool):
        raise ValueError("metric count must equal validation split count")
    accuracy = metrics["accuracy"]
    if isinstance(accuracy, bool) or not isinstance(accuracy, (float, int)):
        raise ValueError("accuracy must be numeric")
    calculated = sum(
        actual == predicted for actual, predicted in zip(labels, predictions, strict=True)
    ) / len(labels)
    if not math.isfinite(accuracy) or not math.isclose(accuracy, calculated, abs_tol=1e-12):
        raise ValueError("accuracy does not match predictions")

    analysis = payload["analysis"]
    if not isinstance(analysis, dict) or set(analysis) != {"error_pattern", "next_experiment"}:
        raise ValueError("analysis requires error_pattern and next_experiment")
    for field in ("error_pattern", "next_experiment"):
        if len(_nonempty_text(analysis[field], field).strip()) < 30:
            raise ValueError(f"{field} needs learner analysis")
    return payload
