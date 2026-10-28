"""Immutable local bundles and an explicit operator trust boundary.

A digest verifies bytes, never trust. Only operator-selected local pickle bundles
may be loaded with trusted_local_artifact=True and an external manifest digest.
Protect the directory/config from concurrent replacement; this is not a sandbox.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import platform
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

from roadmap_tools.experiment_evidence import checked_artifact

from .contracts import (
    Dataset,
    classification_metrics,
    error_rows,
    nonempty,
    normalize_document,
    object_value,
    validate_dataset,
    validate_predictions,
    validate_run,
    validate_sources,
    validate_splits,
)

PREPROCESSING = {"id": "unicode-whitespace-v1", "version": 1, "config": {}}
REQUIRED_ARTIFACTS = {
    "data",
    "splits",
    "sources",
    "model",
    "predictions",
    "metrics",
    "errors",
    "measurement",
    "selection",
}


def json_bytes(value: object) -> bytes:
    """Canonical authored JSON: sorted keys, UTF-8, no NaN, final newline."""
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode(
        "utf-8"
    )


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"nonfinite JSON constant {value}")

    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=unique_pairs,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"unreadable JSON artifact: {path.name}") from exc


@dataclass(frozen=True)
class VerifiedBundle:
    root: Path
    manifest_sha256: str
    manifest: dict[str, Any]
    dataset: Dataset
    splits: Mapping[str, tuple[str, ...]]
    predictions: list[dict[str, str]]
    paths: Mapping[str, Path]


@dataclass(frozen=True)
class LocalClassifier:
    bundle: VerifiedBundle
    model: Any


def _rule_model(value: object, labels: tuple[str, ...]) -> dict[str, Any]:
    model = object_value(value, "rule model")
    if (
        set(model) != {"schema_version", "labels", "rules", "fallback_label"}
        or type(model.get("schema_version")) is not int
        or model["schema_version"] != 1
    ):
        raise ValueError("unsupported rule model schema")
    if model.get("labels") != list(labels) or model.get("fallback_label") not in labels:
        raise ValueError("rule label mapping differs from data")
    if not isinstance(model.get("rules"), list) or not model["rules"]:
        raise ValueError("rules must be nonempty")
    tokens: set[str] = set()
    for raw in model["rules"]:
        rule = object_value(raw, "rule")
        token = nonempty(rule.get("token"), "rule token")
        if (
            set(rule) != {"token", "label"}
            or token != normalize_document(token)
            or " " in token
            or token in tokens
            or rule.get("label") not in labels
        ):
            raise ValueError("invalid rule token/label")
        tokens.add(token)
    return model


def verify_bundle(
    root: Path,
    *,
    expected_manifest_sha256: str,
    exercise_id: str | None = None,
    dataset_sha256: str | None = None,
    split_sha256: str | None = None,
) -> VerifiedBundle:
    """Verify all bytes, schema, split, truth, metrics, sources and error rows.

    The expected manifest digest must come from operator configuration; optional
    expected exercise/data/split identities bind a fixed study. No pickle executes.
    load_trusted_local_classifier additionally checks actual inference parity.
    """
    root = root.resolve()
    try:
        manifest_path = checked_artifact(root, "manifest.json", expected_manifest_sha256)
    except ValueError as exc:
        raise ValueError(f"manifest verification failed: {exc}") from exc
    manifest = object_value(read_json(manifest_path), "manifest")
    inventory = object_value(manifest.get("artifacts"), "artifacts")
    if set(inventory) != REQUIRED_ARTIFACTS:
        raise ValueError("artifact inventory differs from schema")
    paths: dict[str, Path] = {}
    for key, raw in inventory.items():
        entry = object_value(raw, "artifact")
        if set(entry) != {"path", "sha256", "size_bytes"}:
            raise ValueError("invalid artifact entry")
        path = checked_artifact(root, entry["path"], entry["sha256"])
        if type(entry["size_bytes"]) is not int or path.stat().st_size != entry["size_bytes"]:
            raise ValueError("artifact size_bytes differs from saved bytes")
        if path in paths.values() or path == manifest_path:
            raise ValueError("artifact paths must be distinct")
        paths[key] = path
    dataset = validate_dataset(read_json(paths["data"]))
    splits = validate_splits(read_json(paths["splits"]), dataset)
    validate_sources(read_json(paths["sources"]), dataset)
    predictions = validate_predictions(read_json(paths["predictions"]), dataset, splits["test"])
    actual_dataset_sha256 = file_sha256(paths["data"])
    actual_split_sha256 = file_sha256(paths["splits"])
    if dataset_sha256 is not None and dataset_sha256 != actual_dataset_sha256:
        raise ValueError("dataset_sha256 identity differs from actual data bytes")
    if split_sha256 is not None and split_sha256 != actual_split_sha256:
        raise ValueError("split_sha256 identity differs from actual split bytes")
    validate_run(
        manifest,
        dataset,
        splits,
        predictions,
        read_json(paths["metrics"]),
        read_json(paths["errors"]),
        read_json(paths["measurement"]),
        read_json(paths["selection"]),
        exercise_id=exercise_id
        if exercise_id is not None
        else nonempty(manifest.get("exercise_id"), "exercise_id"),
        dataset_sha256=actual_dataset_sha256,
        split_sha256=actual_split_sha256,
    )
    if manifest["model"]["format"] == "rules-json-v1":
        _rule_model(read_json(paths["model"]), dataset.labels)
    return VerifiedBundle(
        root, expected_manifest_sha256, manifest, dataset, splits, predictions, paths
    )


def predict_documents(classifier: LocalClassifier, texts: Sequence[str]) -> list[str]:
    """Predict 1..128 raw documents, each 1..10000 characters, with saved preprocessing."""
    if (
        isinstance(texts, (str, bytes))
        or not isinstance(texts, Sequence)
        or not 1 <= len(texts) <= 128
    ):
        raise ValueError("texts must be a bounded nonempty sequence")
    if any(not isinstance(text, str) or not text.strip() or len(text) > 10000 for text in texts):
        raise ValueError("each text must be nonempty and at most 10000 characters")
    normalized = [normalize_document(text) for text in texts]
    if classifier.bundle.manifest["model"]["format"] == "rules-json-v1":
        model = classifier.model
        predicted = [
            next(
                (rule["label"] for rule in model["rules"] if rule["token"] in text.split()),
                model["fallback_label"],
            )
            for text in normalized
        ]
    else:
        predicted = [str(value) for value in classifier.model.predict(normalized)]
    if len(predicted) != len(texts) or any(
        label not in classifier.bundle.dataset.labels for label in predicted
    ):
        raise ValueError("model produced incompatible labels")
    return predicted


def load_trusted_local_classifier(
    root: Path, expected_manifest_sha256: str, *, trusted_local_artifact: bool = False
) -> LocalClassifier:
    """Load safe JSON, or explicitly trusted operator-selected local sklearn pickle.

    Verify bytes/schema/packages before executable deserialization, then replay the
    fixed test predictions. Never expose the path, digest or trust flag in a request.
    """
    bundle = verify_bundle(root, expected_manifest_sha256=expected_manifest_sha256)
    if bundle.manifest["model"]["format"] == "rules-json-v1":
        model = _rule_model(read_json(bundle.paths["model"]), bundle.dataset.labels)
    else:
        if trusted_local_artifact is not True:
            raise ValueError("pickle requires an explicitly trusted local artifact")
        import numpy
        import sklearn
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline

        expected = bundle.manifest["versions"]
        actual = {
            "sklearn": sklearn.__version__,
            "numpy": numpy.__version__,
            "scipy": version("scipy"),
        }
        if (
            any(expected.get(key) != value for key, value in actual.items())
            or expected["python"].split(".")[:2] != platform.python_version().split(".")[:2]
        ):
            raise ValueError("pickle package/python version incompatibility")
        # This flag expresses operator trust; a digest alone never permits this call.
        model = pickle.loads(bundle.paths["model"].read_bytes())
        if (
            not isinstance(model, Pipeline)
            or len(model.steps) != 2
            or not isinstance(model.steps[0][1], TfidfVectorizer)
            or not isinstance(model.steps[1][1], LogisticRegression)
        ):
            raise ValueError("unsupported sklearn pipeline")
        if set(str(label) for label in model.classes_) != set(bundle.dataset.labels):
            raise ValueError("pipeline label mapping differs from dataset")
    classifier = LocalClassifier(bundle, model)
    ids = bundle.splits["test"]
    actual_predictions = predict_documents(
        classifier, [bundle.dataset.by_id[row].text for row in ids]
    )
    if actual_predictions != [row["predicted_label"] for row in bundle.predictions]:
        raise ValueError("actual reload predictions differ from saved predictions")
    return classifier


def write_run_new(
    output: Path,
    *,
    data: Path,
    splits: Path,
    sources: Path,
    model: bytes,
    predictions: list[dict[str, str]],
    manifest: dict[str, Any],
    measurement: dict[str, Any],
    selection: dict[str, Any],
) -> Path:
    """Write validated run bytes to a NEW directory; never overwrite an existing run.

    Metrics/errors are derived from data and fixed test IDs. Input data/split/source
    bytes are copied exactly; preprocessing is bundled in the rule contract/pipeline.
    Returns manifest.json. Operator must record its digest outside the bundle.
    """
    if output.exists():
        raise FileExistsError(f"run already exists: {output}")
    dataset = validate_dataset(read_json(data))
    partition = validate_splits(read_json(splits), dataset)
    validate_sources(read_json(sources), dataset)
    checked = validate_predictions(predictions, dataset, partition["test"])
    metrics = classification_metrics(dataset, partition["test"], checked)
    errors = error_rows(dataset, checked)
    validate_run(
        manifest,
        dataset,
        partition,
        checked,
        metrics,
        errors,
        measurement,
        selection,
        exercise_id=nonempty(manifest.get("exercise_id"), "exercise_id"),
        dataset_sha256=file_sha256(data),
        split_sha256=file_sha256(splits),
    )
    rule_format = manifest["model"]["format"] == "rules-json-v1"
    if rule_format:
        _rule_model(json.loads(model), dataset.labels)
    files = {
        "data": ("data.json", data.read_bytes()),
        "splits": ("splits.json", splits.read_bytes()),
        "sources": ("sources.json", sources.read_bytes()),
        "model": ("model.json" if rule_format else "model.pkl", model),
        "predictions": ("predictions.json", json_bytes(checked)),
        "metrics": ("metrics.json", json_bytes(metrics)),
        "errors": ("errors.json", json_bytes(errors)),
        "measurement": ("measurement.json", json_bytes(measurement)),
        "selection": ("selection.json", json_bytes(selection)),
    }
    saved_manifest = dict(manifest)
    saved_manifest["artifacts"] = {
        logical: {
            "path": name,
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
        }
        for logical, (name, content) in files.items()
    }
    manifest_bytes = json_bytes(saved_manifest)
    output.mkdir(parents=True, exist_ok=False)
    for name, content in files.values():
        (output / name).write_bytes(content)
    path = output / "manifest.json"
    path.write_bytes(manifest_bytes)
    verify_bundle(output, expected_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest())
    return path
