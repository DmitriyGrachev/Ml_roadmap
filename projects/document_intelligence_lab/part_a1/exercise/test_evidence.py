"""Test-owned complete evidence; never a saved student result or teacher solution."""

from __future__ import annotations

import hashlib
import importlib
import json
import pickle
import platform
import socket
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pytest

from ...artifacts import PREPROCESSING, file_sha256, json_bytes, read_json, write_run_new
from ...contracts import normalize_document, validate_dataset, validate_splits

FIXTURES = Path(__file__).parent / "fixtures"


def validator() -> Any:
    try:
        return importlib.import_module(
            "projects.document_intelligence_lab.part_a1.exercise.protocol"
        )
    except ModuleNotFoundError:
        pytest.fail("independent reproduction validator is missing")


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)


@pytest.fixture
def completed_evidence(tmp_path: Path) -> Path:
    """A deliberately weak test model proves arithmetic/replay, not learner quality."""
    import numpy
    import sklearn
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    dataset = validate_dataset(read_json(FIXTURES / "data.json"))
    splits = validate_splits(read_json(FIXTURES / "splits.json"), dataset)
    rows = dataset.by_id
    root = tmp_path / "evidence"
    root.mkdir()
    models: dict[str, Any] = {
        "rules": {
            "schema_version": 1,
            "labels": list(dataset.labels),
            "rules": [{"token": "borrow", "label": "borrowing"}],
            "fallback_label": "access",
        },
        "tfidf-linear": Pipeline(
            [
                ("tfidf", TfidfVectorizer()),
                ("classifier", LogisticRegression(random_state=23, max_iter=200)),
            ]
        ).fit(
            [normalize_document(rows[row].text) for row in splits["train"]],
            [rows[row].label for row in splits["train"]],
        ),
    }
    references = {}
    for method, model in models.items():
        started = time.perf_counter()
        if method == "rules":
            labels = ["access"] * len(splits["test"])
            payload = json_bytes(model)
        else:
            labels = [
                str(value)
                for value in model.predict(
                    [normalize_document(rows[row].text) for row in splits["test"]]
                )
            ]
            payload = pickle.dumps(model)
        elapsed = time.perf_counter() - started
        manifest = {
            "schema_version": 1,
            "exercise_id": "document-a1-reproduction",
            "dataset_sha256": file_sha256(FIXTURES / "data.json"),
            "split_sha256": file_sha256(FIXTURES / "splits.json"),
            "config": {
                "seed": 23,
                "selection_protocol": "fixed candidates; validation macro_f1; name tie",
            },
            "method": method,
            "evidence_kind": "STUDENT_OFFLINE_REPRODUCTION",
            "run_id": f"test-owned-{method}",
            "code": {
                "revision": "test-fixture",
                "dirty": True,
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            },
            "versions": {
                "python": platform.python_version(),
                "numpy": numpy.__version__,
                "scipy": version("scipy"),
                "sklearn": sklearn.__version__,
            },
            "labels": list(dataset.labels),
            "preprocessing": PREPROCESSING,
            "model": {
                "id": f"fixture-{method}",
                "revision": "1",
                "format": "rules-json-v1" if method == "rules" else "sklearn-pickle-v1",
            },
        }
        path = write_run_new(
            root / method,
            data=FIXTURES / "data.json",
            splits=FIXTURES / "splits.json",
            sources=FIXTURES / "sources.json",
            model=payload,
            predictions=[
                {"row_id": row_id, "predicted_label": label}
                for row_id, label in zip(splits["test"], labels, strict=True)
            ],
            manifest=manifest,
            measurement={
                "timings": [
                    {
                        "name": "fixture",
                        "value": elapsed,
                        "unit": "seconds",
                        "device": "cpu",
                        "sample_count": 6,
                        "batch_size": 6,
                        "condition": "cold",
                    }
                ],
                "memory_bytes": None,
                "memory_unknown_reason": (
                    "Test fixture only; not a claimed measured learner experiment."
                ),
            },
            selection={"criterion": "fixed candidates on validation", "selected_method": method},
        )
        references[method] = {"path": method, "manifest_sha256": file_sha256(path)}
    (root / "report.json").write_bytes(
        json_bytes(
            {
                "schema_version": 1,
                "exercise_id": "document-a1-reproduction",
                "bundles": references,
                "analysis": {
                    "source_permission": "Synthetic author fixture CC0 only.",
                    "annotation_ambiguity": "Multiple actions require review.",
                    "selection_reason": (
                        "Test fixture model chosen to exercise replay, not quality."
                    ),
                    "error_analysis": "The fallback wrongly labels all activity invitations.",
                    "changed_requirement": "Hold out a new notice family before selecting a model.",
                },
            }
        )
    )
    return root


def test_complete_test_owned_evidence_passes_and_replays(completed_evidence: Path) -> None:
    result = validator().validate_reproduction(completed_evidence, trusted_local_artifact=True)
    assert result["mechanical_status"] == "VERIFIED"
    assert result["learner_mastery"] == "REQUIRES_REVIEW"
    assert result["methods"] == ["rules", "tfidf-linear"]


@pytest.mark.parametrize("version", [True, 1.0])
def test_reproduction_schema_version_requires_integer_type(
    completed_evidence: Path, version: object
) -> None:
    report_path = completed_evidence / "report.json"
    report = json.loads(report_path.read_text())
    report["schema_version"] = version
    report_path.write_bytes(json_bytes(report))
    with pytest.raises(ValueError, match="schema"):
        validator().validate_reproduction(completed_evidence, trusted_local_artifact=True)


@pytest.mark.parametrize(
    "change",
    [
        "empty",
        "missing-method",
        "bad-path",
        "digest",
        "wrong-study",
        "teacher-kind",
        "wrong-metrics",
        "inference-disagrees",
    ],
)
def test_malformed_completed_evidence_fails(completed_evidence: Path, change: str) -> None:
    report_path = completed_evidence / "report.json"
    report = json.loads(report_path.read_text())
    if change == "empty":
        report["analysis"]["error_analysis"] = ""
    elif change == "missing-method":
        del report["bundles"]["tfidf-linear"]
    elif change == "bad-path":
        report["bundles"]["rules"]["path"] = "../outside"
    elif change == "digest":
        report["bundles"]["rules"]["manifest_sha256"] = "0" * 64
    else:
        root = completed_evidence / "rules"
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        if change == "wrong-study":
            manifest["exercise_id"] = "teacher"
        elif change == "teacher-kind":
            manifest["evidence_kind"] = "AUTHOR_SYNTHETIC_SMOKE_ONLY"
        else:
            logical = "metrics" if change == "wrong-metrics" else "model"
            path = root / manifest["artifacts"][logical]["path"]
            value = json.loads(path.read_text())
            if logical == "metrics":
                value["accuracy"] = 1.0
            else:
                value["fallback_label"] = "event"
            path.write_bytes(json_bytes(value))
            manifest["artifacts"][logical].update(
                sha256=file_sha256(path), size_bytes=path.stat().st_size
            )
        manifest_path.write_bytes(json_bytes(manifest))
        report["bundles"]["rules"]["manifest_sha256"] = file_sha256(manifest_path)
    report_path.write_bytes(json_bytes(report))
    with pytest.raises(
        ValueError,
        match=r"error_analysis|bundles|path|manifest|exercise_id|evidence|metrics|predictions|sha256",
    ):
        validator().validate_reproduction(completed_evidence, trusted_local_artifact=True)


def test_pickle_evidence_needs_deliberate_local_trust(completed_evidence: Path) -> None:
    with pytest.raises(ValueError, match="trusted"):
        validator().validate_reproduction(completed_evidence)
