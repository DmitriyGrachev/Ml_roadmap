"""Small artifact checks; checking evidence does not write the learner's analysis."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from pathlib import Path, PureWindowsPath
from typing import Any

METHODS = {"tfidf_linear", "frozen_embeddings", "adapted_encoder"}
PREPROCESSING = "nfkc-casefold-space-v1"


def verify_file(path: Path, checksum: str, size_bytes: int | None = None) -> str:
    if not path.is_file():
        raise ValueError(f"artifact missing: {path}")
    if size_bytes is not None and path.stat().st_size != size_bytes:
        raise ValueError(f"size mismatch: {path}")
    with path.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != checksum:
        raise ValueError(f"checksum mismatch: {path}")
    return actual


def artifact_path(root: Path, name: str) -> Path:
    if not name or "\\" in name or Path(name).anchor or PureWindowsPath(name).anchor:
        raise ValueError("artifact path must be a relative portable name")
    resolved = (root / name).resolve()
    if ".." in Path(name).parts or not resolved.is_relative_to(root.resolve()):
        raise ValueError("artifact path escapes report directory")
    if not resolved.is_file():
        raise ValueError(f"artifact missing: {name}")
    return resolved


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"report is missing or invalid: {path}") from error
    if not isinstance(value, dict):
        raise ValueError("report must be a JSON object")
    return value


def metrics(labels: Sequence[int], predictions: Sequence[int]) -> tuple[float, float]:
    from sklearn.metrics import accuracy_score, f1_score

    if not labels or len(labels) != len(predictions):
        raise ValueError("predictions must align with nonempty labels")
    if any(type(value) is not int or value not in range(4) for value in (*labels, *predictions)):
        raise ValueError("labels must be integer IDs 0..3")
    return (
        float(accuracy_score(labels, predictions)),
        float(f1_score(labels, predictions, labels=[0, 1, 2, 3], average="macro", zero_division=0)),
    )


def validate_comparison(reports: Mapping[str, Any], labels: Sequence[int]) -> None:
    if set(reports) != METHODS:
        raise ValueError("report must compare exactly the three methods")
    for report in reports.values():
        accuracy, macro_f1 = metrics(labels, report.get("predictions", []))
        for name, computed in (("accuracy", accuracy), ("macro_f1", macro_f1)):
            value = report.get(name)
            if not isinstance(value, (int, float)) or not math.isclose(
                value, computed, abs_tol=1e-8
            ):
                raise ValueError(f"{name} differs from computed predictions")
        elapsed = report.get("warm_seconds")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("warm_seconds must be a measured finite duration")
        memory = report.get("peak_memory_bytes")
        if memory is not None and (type(memory) is not int or memory <= 0):
            raise ValueError("peak_memory_bytes must be positive or null")
        if not isinstance(report.get("memory_note"), str) or not report["memory_note"].strip():
            raise ValueError("memory_note must describe the measurement or NOT_MEASURED reason")


def checkpoint_predictions(
    checkpoint: Path, texts: Sequence[str], *, batch_size: int, max_length: int
) -> list[int]:
    """Recompute evidence from local saved bytes; never load a Hub identifier."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model = AutoModelForSequenceClassification.from_pretrained(
        checkpoint, local_files_only=True, trust_remote_code=False, use_safetensors=True
    ).eval()
    tokenizer = AutoTokenizer.from_pretrained(
        checkpoint, local_files_only=True, trust_remote_code=False
    )
    predictions: list[int] = []
    with torch.inference_mode():
        for offset in range(0, len(texts), batch_size):
            batch = tokenizer(
                list(texts[offset : offset + batch_size]),
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            predictions.extend(model(**batch).logits.argmax(dim=1).tolist())
    return predictions


def validate_offline_artifacts(root: Path) -> dict[str, Any]:
    report = read_object(root / "offline-report.json")
    if report.get("evidence") != "LOCAL_RANDOM_ENCODER_STUDENT_RUN":
        raise ValueError("offline report evidence cannot claim pretrained/live quality")
    if report.get("schema_version") != 1 or report.get("pretrained_quality") != "NOT_RUN":
        raise ValueError("report schema/pretrained_quality invalid")
    if type(report.get("seed")) is not int or report["seed"] < 0:
        raise ValueError("seed must be a nonnegative integer")
    revision = report.get("code_revision")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("code_revision must record a full Git commit SHA")
    for field in ("data", "splits"):
        record = report.get(field, {})
        verify_file(artifact_path(root, record.get("path", "")), record.get("sha256", ""))
    files = report.get("checkpoint_files", {})
    required = {
        "checkpoint/model.safetensors",
        "checkpoint/config.json",
        "checkpoint/tokenizer.json",
    }
    if not isinstance(files, dict) or not required.issubset(files):
        raise ValueError("checkpoint_files must identify actual model and tokenizer files")
    for name, checksum in files.items():
        if not name.startswith("checkpoint/") or name.endswith((".bin", ".pkl", ".pt")):
            raise ValueError("checkpoint artifact must use safetensors/JSON tokenizer files")
        verify_file(artifact_path(root, name), checksum)
    splits = read_object(artifact_path(root, report["splits"]["path"]))
    if set(splits) != {"train", "validation", "test"}:
        raise ValueError("splits must identify train/validation/test")
    all_ids: list[str] = []
    for records in splits.values():
        if (
            not isinstance(records, list)
            or not records
            or any(not isinstance(x, str) for x in records)
        ):
            raise ValueError("split IDs must be nonempty string lists")
        all_ids.extend(records)
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("split overlap detected")
    data = read_object(artifact_path(root, report["data"]["path"]))
    records = data.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("data must contain saved records")
    by_id: dict[str, dict[str, Any]] = {}
    content_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != {"row_id", "text", "label"}:
            raise ValueError("data records must contain row_id/text/label")
        identifier, text, label = record["row_id"], record["text"], record["label"]
        if not isinstance(identifier, str) or not identifier or identifier in by_id:
            raise ValueError("data IDs must be unique nonempty strings")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("data text must be nonempty")
        if type(label) is not int or label not in range(4):
            raise ValueError("data label must be in 0..3")
        normalized = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
        if normalized in content_ids:
            raise ValueError("data contains duplicate normalized text")
        content_ids.add(normalized)
        by_id[identifier] = record
    if set(all_ids) != set(by_id):
        raise ValueError("splits must partition exactly the saved data IDs")
    if report.get("test_ids") != splits["test"]:
        raise ValueError("test predictions must follow frozen test IDs")
    accuracy, macro_f1 = metrics(report.get("labels", []), report.get("predictions", []))
    if len(report["labels"]) != len(splits["test"]):
        raise ValueError("labels must align with test IDs")
    if report["labels"] != [by_id[identifier]["label"] for identifier in splits["test"]]:
        raise ValueError("reported labels differ from saved test records")
    for name, computed in (("accuracy", accuracy), ("macro_f1", macro_f1)):
        if not isinstance(report.get(name), (int, float)) or not math.isclose(
            report[name], computed, abs_tol=1e-8
        ):
            raise ValueError(f"{name} differs from computed predictions")
    if report.get("model") != {"id": "local-random-bert", "revision": "fixture-v1"}:
        raise ValueError("model identity must identify the local random fixture")
    if not isinstance(report.get("versions"), dict) or not all(
        isinstance(report["versions"].get(name), str) and report["versions"][name]
        for name in ("python", "torch", "transformers", "datasets", "scikit_learn")
    ):
        raise ValueError("versions must identify the experiment environment")
    config = report.get("config", {})
    if not isinstance(config, dict) or not all(
        type(config.get(name)) is int and config[name] > 0
        for name in ("batch_size", "max_length", "max_steps")
    ):
        raise ValueError("config must record positive batch_size/max_length/max_steps")
    rate = config.get("learning_rate")
    if (
        isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(rate)
        or rate <= 0
    ):
        raise ValueError("learning_rate must be finite and positive")
    if config.get("preprocessing") != PREPROCESSING:
        raise ValueError(f"preprocessing must be {PREPROCESSING}")
    analysis = artifact_path(root, "analysis.md").read_text(encoding="utf-8").strip()
    if len(analysis) < 200 or any(
        token in analysis.lower() for token in ("todo", "fill me", "lorem ipsum")
    ):
        raise ValueError("analysis must contain the learner's explanation, not placeholders")
    test_text = [by_id[identifier]["text"] for identifier in splits["test"]]
    actual_predictions = checkpoint_predictions(
        root / "checkpoint",
        test_text,
        batch_size=config["batch_size"],
        max_length=config["max_length"],
    )
    if actual_predictions != report["predictions"]:
        raise ValueError("reported results differ from checkpoint predictions")
    return report
