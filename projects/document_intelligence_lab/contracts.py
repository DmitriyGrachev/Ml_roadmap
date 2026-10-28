"""Schema 1 for document classification, independent of the model implementation.

Text fingerprints hash the exact UTF-8 text. Leakage normalization is NFKC,
casefold and whitespace collapse; it cannot detect semantic/template leakage.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from roadmap_tools.experiment_evidence import validate_identity


@dataclass(frozen=True)
class Record:
    row_id: str
    text: str
    label: str
    source_id: str
    group_id: str
    content_sha256: str


@dataclass(frozen=True)
class Dataset:
    labels: tuple[str, ...]
    records: tuple[Record, ...]

    @property
    def by_id(self) -> Mapping[str, Record]:
        return MappingProxyType({row.row_id: row for row in self.records})


def object_value(value: object, name: str) -> dict[str, Any]:
    """Validate a JSON object boundary before indexing it."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be an object")
    return value


def nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    return value


def sha256_value(value: object, name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{name} must be lowercase SHA-256")
    return value


def normalize_document(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def validate_dataset(value: object) -> Dataset:
    data = object_value(value, "data")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported data schema_version")
    labels = data.get("labels")
    if not isinstance(labels, list) or len(labels) < 2:
        raise ValueError("labels must be an ordered list of at least two labels")
    for label in labels:
        nonempty(label, "label")
    if len(set(labels)) != len(labels):
        raise ValueError("duplicate labels")
    raw = data.get("records")
    if not isinstance(raw, list) or not raw:
        raise ValueError("records must be nonempty")
    rows: list[Record] = []
    seen: set[str] = set()
    for item in raw:
        row = object_value(item, "record")
        if set(row) != {"row_id", "text", "label", "source_id", "group_id", "content_sha256"}:
            raise ValueError("record fields differ from schema")
        values = {key: nonempty(value, key) for key, value in row.items()}
        if values["row_id"] in seen or values["label"] not in labels:
            raise ValueError("duplicate row_id or unknown label")
        if hashlib.sha256(values["text"].encode("utf-8")).hexdigest() != values["content_sha256"]:
            raise ValueError("content_sha256 differs from exact text bytes")
        seen.add(values["row_id"])
        rows.append(Record(**values))
    return Dataset(tuple(labels), tuple(rows))


def validate_splits(value: object, dataset: Dataset) -> Mapping[str, tuple[str, ...]]:
    splits = object_value(value, "splits")
    if set(splits) != {"train", "validation", "test"}:
        raise ValueError("splits require exactly train/validation/test")
    accepted: dict[str, tuple[str, ...]] = {}
    assigned: dict[str, str] = {}
    groups: dict[str, str] = {}
    contents: dict[str, str] = {}
    rows = dataset.by_id
    for part in ("train", "validation", "test"):
        ids = splits[part]
        if not isinstance(ids, list) or not ids:
            raise ValueError("each split must be a nonempty ordered list")
        for row_id in ids:
            if not isinstance(row_id, str) or row_id not in rows or row_id in assigned:
                raise ValueError("unknown/duplicate split row_id")
            row = rows[row_id]
            for table, key in ((groups, row.group_id), (contents, normalize_document(row.text))):
                if key in table and table[key] != part:
                    raise ValueError("group or normalized exact duplicate crosses splits")
                table[key] = part
            assigned[row_id] = part
        accepted[part] = tuple(ids)
    if set(assigned) != set(rows):
        raise ValueError("splits must partition all accepted row IDs")
    return MappingProxyType(accepted)


def validate_sources(value: object, dataset: Dataset) -> None:
    sources = object_value(value, "sources")
    if type(sources.get("schema_version")) is not int or sources["schema_version"] != 1:
        raise ValueError("unsupported sources schema_version")
    nonempty(sources.get("annotation_policy"), "annotation_policy")
    rows = sources.get("sources")
    if not isinstance(rows, list) or not rows:
        raise ValueError("sources must be nonempty")
    ids: set[str] = set()
    for value in rows:
        row = object_value(value, "source")
        source_id = nonempty(row.get("source_id"), "source_id")
        if source_id in ids:
            raise ValueError("duplicate source_id")
        ids.add(source_id)
        nonempty(row.get("permission"), "source permission")
        nonempty(row.get("license"), "source license")
    if not {row.source_id for row in dataset.records}.issubset(ids):
        raise ValueError("dataset has an undocumented source_id")


def validate_predictions(
    value: object, dataset: Dataset, evaluation_ids: Sequence[str]
) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) != len(evaluation_ids) or not value:
        raise ValueError("predictions must match all evaluation IDs")
    result: list[dict[str, str]] = []
    for raw, expected in zip(value, evaluation_ids, strict=True):
        row = object_value(raw, "prediction")
        if set(row) != {"row_id", "predicted_label"}:
            raise ValueError(
                "prediction requires only row_id and predicted_label; truth is in data"
            )
        if row.get("row_id") != expected or row.get("predicted_label") not in dataset.labels:
            raise ValueError("prediction ID order or label differs from contract")
        if expected not in dataset.by_id:
            raise ValueError("unknown evaluation ID")
        result.append({"row_id": expected, "predicted_label": row["predicted_label"]})
    return result


def classification_metrics(
    dataset: Dataset, evaluation_ids: Sequence[str], predictions: object
) -> dict[str, Any]:
    rows = validate_predictions(predictions, dataset, evaluation_ids)
    positions = {label: index for index, label in enumerate(dataset.labels)}
    matrix = [[0 for _ in dataset.labels] for _ in dataset.labels]
    for row in rows:
        truth = dataset.by_id[row["row_id"]].label
        matrix[positions[truth]][positions[row["predicted_label"]]] += 1
    f1 = []
    for i in range(len(dataset.labels)):
        denominator = sum(matrix[i]) + sum(row[i] for row in matrix)
        f1.append(2 * matrix[i][i] / denominator if denominator else 0.0)
    return {
        "count": len(rows),
        "accuracy": sum(matrix[i][i] for i in range(len(matrix))) / len(rows),
        "macro_f1": sum(f1) / len(dataset.labels),
        "confusion": matrix,
        "label_order": list(dataset.labels),
        "zero_division": 0,
    }


def error_rows(dataset: Dataset, predictions: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "row_id": row["row_id"],
            "true_label": dataset.by_id[row["row_id"]].label,
            "predicted_label": row["predicted_label"],
            "category": "misclassification",
            "analysis_status": "REQUIRES_REVIEW",
        }
        for row in predictions
        if dataset.by_id[row["row_id"]].label != row["predicted_label"]
    ]


def validate_measurement(value: object) -> None:
    measurement = object_value(value, "measurement")
    timings = measurement.get("timings")
    if not isinstance(timings, list) or not timings:
        raise ValueError("measured timings are required")
    for raw in timings:
        row = object_value(raw, "timing")
        nonempty(row.get("name"), "timing name")
        if row.get("unit") != "seconds" or row.get("device") != "cpu":
            raise ValueError("A1 timing units/device must be seconds/cpu")
        if row.get("condition") not in ("cold", "warm"):
            raise ValueError("timing condition must be cold/warm")
        number = row.get("value")
        if (
            isinstance(number, bool)
            or not isinstance(number, (int, float))
            or not math.isfinite(number)
            or number < 0
        ):
            raise ValueError("timing must be finite nonnegative measured value")
        for key in ("sample_count", "batch_size"):
            if type(row.get(key)) is not int or row[key] < 1:
                raise ValueError("timing counts must be positive integers")
    memory = measurement.get("memory_bytes")
    if memory is None:
        nonempty(measurement.get("memory_unknown_reason"), "memory_unknown_reason")
    elif type(memory) is not int or memory < 0:
        raise ValueError("memory must be nonnegative bytes or null with reason")


def validate_run(
    manifest: object,
    dataset: Dataset,
    splits: Mapping[str, tuple[str, ...]],
    predictions: object,
    metrics: object,
    errors: object,
    measurement: object,
    selection: object,
    *,
    exercise_id: str,
    dataset_sha256: str,
    split_sha256: str,
) -> None:
    run = object_value(manifest, "manifest")
    validate_identity(
        run, exercise_id=exercise_id, dataset_sha256=dataset_sha256, split_sha256=split_sha256
    )
    for key in ("method", "evidence_kind", "run_id"):
        nonempty(run.get(key), key)
    if run.get("labels") != list(dataset.labels):
        raise ValueError("manifest label order differs from dataset")
    config = object_value(run["config"], "config")
    if type(config.get("seed")) is not int or config["seed"] < 0:
        raise ValueError("config seed must be nonnegative integer")
    code = object_value(run.get("code"), "code")
    nonempty(code.get("revision"), "code revision")
    if type(code.get("dirty")) is not bool:
        raise ValueError("code dirty must be boolean")
    sha256_value(code.get("source_sha256"), "code source_sha256")
    versions = object_value(run.get("versions"), "versions")
    nonempty(versions.get("python"), "python version")
    preprocessing = object_value(run.get("preprocessing"), "preprocessing")
    if type(preprocessing.get("version")) is not int or preprocessing != {
        "id": "unicode-whitespace-v1",
        "version": 1,
        "config": {},
    }:
        raise ValueError("unsupported preprocessing identity/config")
    model = object_value(run.get("model"), "model")
    for key in ("id", "revision"):
        nonempty(model.get(key), f"model {key}")
    if model.get("format") not in ("rules-json-v1", "sklearn-pickle-v1"):
        raise ValueError("unsupported model format")
    if model["format"] == "sklearn-pickle-v1":
        for name in ("sklearn", "numpy", "scipy"):
            nonempty(versions.get(name), f"{name} version")
    checked = validate_predictions(predictions, dataset, splits["test"])
    saved_metrics = object_value(metrics, "metrics")
    matrix = saved_metrics.get("confusion")
    if (
        type(saved_metrics.get("count")) is not int
        or type(saved_metrics.get("zero_division")) is not int
        or not isinstance(matrix, list)
        or any(
            not isinstance(row, list) or any(type(count) is not int for count in row)
            for row in matrix
        )
        or any(
            isinstance(saved_metrics.get(key), bool)
            or not isinstance(saved_metrics.get(key), (int, float))
            for key in ("accuracy", "macro_f1")
        )
    ):
        raise ValueError("metrics require numeric values and integer counts, never booleans")
    if metrics != classification_metrics(dataset, splits["test"], checked):
        raise ValueError("metrics differ from verified predictions")
    if errors != error_rows(dataset, checked):
        raise ValueError("errors differ from actual predictions")
    validate_measurement(measurement)
    chosen = object_value(selection, "selection")
    nonempty(chosen.get("criterion"), "selection criterion")
    if chosen.get("selected_method") != run["method"]:
        raise ValueError("selection method differs from manifest")
