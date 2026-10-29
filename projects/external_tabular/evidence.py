"""Portable, offline artifact arithmetic shared by the two external projects.

Hashes establish internal consistency, not provenance authenticity or authorship.
Only each project's validate_submission is a credit gate.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections.abc import Sequence
from pathlib import Path, PureWindowsPath
from typing import Any

METHODS = {
    "ml-external-tabular": {"dummy", "linear", "tree"},
    "document-external-model-study": {"tfidf_linear", "frozen_embeddings", "adapted_encoder"},
}
CENTRAL_COMPARISON = {
    "ml-external-tabular": ("linear", "tree"),
    "document-external-model-study": ("tfidf_linear", "adapted_encoder"),
}


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"missing or invalid JSON: {path.name}") from error
    if not isinstance(value, dict):
        raise ValueError("JSON artifact must be an object")
    return value


def nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    return value


def artifact_path(root: Path, name: str) -> Path:
    nonempty(name, "artifact path")
    if "\\" in name or PureWindowsPath(name).anchor or Path(name).is_absolute():
        raise ValueError("artifact path must be relative and portable")
    path = (root / name).resolve()
    if ".." in Path(name).parts or not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("artifact path missing or escapes submission")
    return path


def finite(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def classification_metrics(
    labels: Sequence[int], predictions: Sequence[int], classes: Sequence[int]
) -> dict[str, Any]:
    if not labels or len(labels) != len(predictions):
        raise ValueError("labels/predictions must be nonempty and aligned")
    if any(type(x) is not int or x not in classes for x in (*labels, *predictions)):
        raise ValueError("labels/predictions must use integer class IDs")
    confusion = [[0 for _ in classes] for _ in classes]
    positions = {label: index for index, label in enumerate(classes)}
    for truth, prediction in zip(labels, predictions, strict=True):
        confusion[positions[truth]][positions[prediction]] += 1
    f1 = []
    for index in range(len(classes)):
        denominator = sum(confusion[index]) + sum(row[index] for row in confusion)
        f1.append(2 * confusion[index][index] / denominator if denominator else 0.0)
    return {
        "count": len(labels),
        "accuracy": sum(t == p for t, p in zip(labels, predictions, strict=True)) / len(labels),
        "macro_f1": sum(f1) / len(f1),
        "confusion": confusion,
    }


def paired_bootstrap(
    labels: Sequence[int], baseline: Sequence[int], candidate: Sequence[int], classes: Sequence[int]
) -> dict[str, Any]:
    """Fixed 1000 paired IID resamples, seed 17; not training/split uncertainty."""
    left = classification_metrics(labels, baseline, classes)["macro_f1"]
    right = classification_metrics(labels, candidate, classes)["macro_f1"]
    rng = random.Random(17)
    differences = []
    for _ in range(1000):
        indices = [rng.randrange(len(labels)) for _ in labels]
        sampled = [labels[i] for i in indices]
        differences.append(
            classification_metrics(sampled, [candidate[i] for i in indices], classes)["macro_f1"]
            - classification_metrics(sampled, [baseline[i] for i in indices], classes)["macro_f1"]
        )
    differences.sort()
    return {
        "seed": 17,
        "resamples": 1000,
        "unit": "row",
        "metric": "macro_f1",
        "difference": right - left,
        "low": differences[24],
        "high": differences[974],
        "scope": "conditional_on_fixed_predictions_iid_rows",
    }


def submission_or_incomplete(root: Path) -> Path:
    if not (root / "manifest.json").exists():
        raise NotImplementedError(f"Создайте собственную submission: {root}")
    return root


def check_equal(actual: object, expected: object, name: str) -> None:
    """Strict JSON types prevent true == 1 and nested NaN from passing arithmetic checks."""
    if json.dumps(actual, sort_keys=True, allow_nan=False) != json.dumps(
        expected, sort_keys=True, allow_nan=False
    ):
        raise ValueError(f"{name} differs from recomputed evidence")


def validate_bundle(root: Path, *, project_id: str, author_fixture: bool = False) -> dict[str, Any]:
    manifest = read_json(root / "manifest.json")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError("schema_version must be integer 1")
    if manifest.get("project_id") != project_id:
        raise ValueError("project_id differs")
    expected = "AUTHOR_FIXTURE_ONLY" if author_fixture else "INDEPENDENT_EXTERNAL_RUN"
    if manifest.get("evidence_kind") != expected:
        raise ValueError("evidence_kind must identify external work, never author fixture")
    refs = manifest.get("artifacts")
    required = {"raw", "data", "splits", "evaluation", "source", "code", "analysis"}
    if not isinstance(refs, dict) or not required.issubset(refs):
        raise ValueError("required artifact references missing")
    files: dict[str, Path] = {}
    for key, ref in refs.items():
        if not isinstance(ref, dict):
            raise ValueError("artifact reference must be an object")
        path = artifact_path(root, ref.get("path", ""))
        if ref.get("sha256") != sha256(path):
            raise ValueError(f"artifact sha256 mismatch: {key}")
        files[key] = path
    if len(set(files.values())) != len(files):
        raise ValueError("logical artifacts must refer to separate files")
    nonempty(files["code"].read_text(encoding="utf-8"), "experiment code")
    nonempty(files["analysis"].read_text(encoding="utf-8"), "analysis")
    source = read_json(files["source"])
    for field in ("provider", "url", "license", "retrieved_at", "permission_note"):
        nonempty(source.get(field), f"source {field}")
    if not author_fixture and not source["url"].startswith("https://"):
        raise ValueError("external source URL must be HTTPS")
    data, splits, evaluation = (read_json(files[key]) for key in ("data", "splits", "evaluation"))
    classes = data.get("classes")
    if not isinstance(classes, list) or classes != list(range(len(classes))) or len(classes) < 2:
        raise ValueError("classes must be consecutive IDs starting at zero")
    if any(type(x) is not int for x in classes):
        raise ValueError("class IDs must be integers")
    records = data.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("data records must be nonempty")
    by_id: dict[str, Any] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("record must be an object")
        row_id = nonempty(record.get("row_id"), "row_id")
        nonempty(record.get("group_id"), "group_id")
        label = record.get("label")
        if row_id in by_id or type(label) is not int or label not in classes:
            raise ValueError("duplicate row IDs or invalid label")
        by_id[row_id] = record
    if set(splits) != {"train", "validation", "test"}:
        raise ValueError("splits must be train/validation/test")
    assigned: dict[str, str] = {}
    group_assignment: dict[str, str] = {}
    for part, ids in splits.items():
        if not isinstance(ids, list) or not ids:
            raise ValueError("every split requires ordered nonempty row IDs")
        for row_id in ids:
            if not isinstance(row_id, str) or row_id not in by_id or row_id in assigned:
                raise ValueError("unknown/duplicate row ID or split overlap")
            group = by_id[row_id]["group_id"]
            if group in group_assignment and group_assignment[group] != part:
                raise ValueError("group leakage across splits")
            assigned[row_id] = part
            group_assignment[group] = part
    if set(assigned) != set(by_id):
        raise ValueError("split manifest must partition all data")
    if {by_id[row_id]["label"] for row_id in splits["train"]} != set(classes):
        raise ValueError("training split must contain every class")
    if evaluation.get("row_ids") != splits["test"]:
        raise ValueError("evaluation row ID order differs from locked test manifest")
    labels = [by_id[row_id]["label"] for row_id in splits["test"]]
    check_equal(evaluation.get("labels"), labels, "saved test labels")
    methods = evaluation.get("methods")
    if not isinstance(methods, dict) or set(methods) != METHODS[project_id]:
        raise ValueError("methods must include all mandatory comparisons")
    for name, method in methods.items():
        if not isinstance(method, dict):
            raise ValueError("method must be object")
        computed = classification_metrics(labels, method.get("predictions", []), classes)
        check_equal(method.get("metrics"), computed, f"metrics {name}")
        if not finite(method.get("seconds")) or method["seconds"] < 0:
            raise ValueError("seconds must be finite measured duration")
    comparison = evaluation.get("comparison", {})
    baseline, candidate = comparison.get("baseline"), comparison.get("candidate")
    if baseline not in methods or candidate not in methods or baseline == candidate:
        raise ValueError("paired comparison must name two distinct measured methods")
    if (baseline, candidate) != CENTRAL_COMPARISON[project_id]:
        raise ValueError("paired comparison must use the documented central baseline/candidate")
    check_equal(
        evaluation.get("paired_bootstrap"),
        paired_bootstrap(
            labels, methods[baseline]["predictions"], methods[candidate]["predictions"], classes
        ),
        "paired uncertainty",
    )
    slices = evaluation.get("slices")
    if not isinstance(slices, list) or len(slices) < 2:
        raise ValueError("at least two explicit error slices required")
    slice_names: set[str] = set()
    for slice_ in slices:
        name = nonempty(slice_.get("name"), "slice name")
        ids = slice_.get("row_ids")
        if name in slice_names or not isinstance(ids, list) or not ids or len(set(ids)) != len(ids):
            raise ValueError("slices must have unique names and nonempty unique row IDs")
        slice_names.add(name)
        if not set(ids).issubset(splits["test"]):
            raise ValueError("slice IDs must belong to final evaluation")
        indices = [splits["test"].index(row_id) for row_id in ids]
        expected_metrics = {
            method: classification_metrics(
                [labels[i] for i in indices], [row["predictions"][i] for i in indices], classes
            )
            for method, row in methods.items()
        }
        check_equal(slice_.get("methods"), expected_metrics, "slice metrics")
    return {
        "technical_status": "AUTHOR_FIXTURE_ONLY" if author_fixture else "ARTIFACTS_CONSISTENT",
        "human_review": "REQUIRED",
        "authorship": "NOT_AUTOMATICALLY_VERIFIED",
        "files": files,
        "manifest": manifest,
        "data": data,
        "splits": splits,
        "evaluation": evaluation,
        "source": source,
    }


def make_evaluation(
    data: dict[str, Any],
    splits: dict[str, list[str]],
    methods: dict[str, Any],
    baseline: str,
    candidate: str,
) -> dict[str, Any]:
    """Author/sample utility; learners still choose models, split and interpretation."""
    by_id = {row["row_id"]: row for row in data["records"]}
    ids = splits["test"]
    labels = [by_id[row_id]["label"] for row_id in ids]
    for method in methods.values():
        method["metrics"] = classification_metrics(labels, method["predictions"], data["classes"])
    slices = []
    for label in data["classes"]:
        indices = [i for i, value in enumerate(labels) if value == label]
        if indices:
            slices.append(
                {
                    "name": f"true-label-{label}",
                    "row_ids": [ids[i] for i in indices],
                    "methods": {
                        name: classification_metrics(
                            [labels[i] for i in indices],
                            [row["predictions"][i] for i in indices],
                            data["classes"],
                        )
                        for name, row in methods.items()
                    },
                }
            )
    return {
        "row_ids": ids,
        "labels": labels,
        "methods": methods,
        "slices": slices,
        "comparison": {"baseline": baseline, "candidate": candidate},
        "paired_bootstrap": paired_bootstrap(
            labels,
            methods[baseline]["predictions"],
            methods[candidate]["predictions"],
            data["classes"],
        ),
    }


def write_bundle(
    output: Path, *, project_id: str, evidence_kind: str, payloads: dict[str, tuple[str, bytes]]
) -> None:
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be empty; preserve previous experiments")
    output.mkdir(parents=True, exist_ok=True)
    refs = {}
    for logical, (name, payload) in payloads.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        refs[logical] = {"path": name, "sha256": sha256(target)}
    (output / "manifest.json").write_bytes(
        json_bytes(
            {
                "schema_version": 1,
                "project_id": project_id,
                "evidence_kind": evidence_kind,
                "artifacts": refs,
            }
        )
    )


def json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
