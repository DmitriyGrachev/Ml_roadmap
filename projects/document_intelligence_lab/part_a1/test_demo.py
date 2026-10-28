"""Offline author contract tests; no learner work is imported here."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import math
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


def api(name: str) -> Any:
    try:
        return importlib.import_module(f"projects.document_intelligence_lab.{name}")
    except ModuleNotFoundError:
        pytest.fail(f"A1 {name} implementation is missing")


def encode(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access is forbidden in A1")

    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)


@pytest.fixture
def tiny_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    records = [
        {
            "row_id": row_id,
            "text": text,
            "label": label,
            "source_id": "authored",
            "group_id": row_id,
            "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
        for row_id, text, label in (
            ("r1", "circle red", "circle"),
            ("r2", "square red", "square"),
            ("r3", "triangle blue", "triangle"),
            ("r4", "large circle", "circle"),
            ("r5", "small square", "square"),
            ("r6", "green triangle", "triangle"),
        )
    ]
    values = [
        {"schema_version": 1, "labels": ["circle", "square", "triangle"], "records": records},
        {"train": ["r1", "r2", "r3"], "validation": ["r4"], "test": ["r5", "r6"]},
        {
            "schema_version": 1,
            "sources": [
                {"source_id": "authored", "permission": "author-created", "license": "CC0-1.0"}
            ],
            "annotation_policy": "literal shape; ambiguous texts excluded",
        },
    ]
    paths = tuple(tmp_path / name for name in ("data.json", "splits.json", "sources.json"))
    for path, value in zip(paths, values, strict=True):
        path.write_bytes(encode(value))
    return paths  # type: ignore[return-value]


@pytest.fixture
def rule_bundle(tmp_path: Path, tiny_inputs: tuple[Path, Path, Path]) -> Path:
    artifacts = api("artifacts")
    data, splits, sources = tiny_inputs
    manifest = {
        "schema_version": 1,
        "exercise_id": "test-owned-fixture",
        "dataset_sha256": digest(data),
        "split_sha256": digest(splits),
        "config": {"seed": 17},
        "method": "rules",
        "evidence_kind": "TEST_FIXTURE",
        "run_id": "unit-1",
        "code": {"revision": "test-owned", "dirty": True, "source_sha256": "a" * 64},
        "versions": {"python": f"{sys.version_info.major}.{sys.version_info.minor}"},
        "labels": ["circle", "square", "triangle"],
        "preprocessing": {"id": "unicode-whitespace-v1", "version": 1, "config": {}},
        "model": {"id": "test-rules", "revision": "1", "format": "rules-json-v1"},
    }
    model = {
        "schema_version": 1,
        "labels": manifest["labels"],
        "rules": [{"token": "square", "label": "square"}],
        "fallback_label": "circle",
    }
    artifacts.write_run_new(
        tmp_path / "bundle",
        data=data,
        splits=splits,
        sources=sources,
        model=encode(model),
        predictions=[
            {"row_id": "r5", "predicted_label": "square"},
            {"row_id": "r6", "predicted_label": "circle"},
        ],
        manifest=manifest,
        measurement={
            "timings": [
                {
                    "name": "inference",
                    "value": 0.001,
                    "unit": "seconds",
                    "device": "cpu",
                    "sample_count": 2,
                    "batch_size": 2,
                    "condition": "cold",
                }
            ],
            "memory_bytes": None,
            "memory_unknown_reason": "fixture does not profile memory",
        },
        selection={"criterion": "fixed before test", "selected_method": "rules"},
    )
    return tmp_path / "bundle"


def rewrite_artifact(bundle: Path, logical: str, value: object) -> None:
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entry = manifest["artifacts"][logical]
    path = bundle / entry["path"]
    path.write_bytes(encode(value))
    entry.update(sha256=digest(path), size_bytes=path.stat().st_size)
    manifest_path.write_bytes(encode(manifest))


def verify(bundle: Path) -> Any:
    return api("artifacts").verify_bundle(
        bundle, expected_manifest_sha256=digest(bundle / "manifest.json")
    )


def test_metrics_use_full_label_universe_and_truth_from_data(
    tiny_inputs: tuple[Path, Path, Path],
) -> None:
    contracts = api("contracts")
    dataset = contracts.validate_dataset(json.loads(tiny_inputs[0].read_text()))
    splits = contracts.validate_splits(json.loads(tiny_inputs[1].read_text()), dataset)
    rows = [
        {"row_id": "r5", "predicted_label": "square"},
        {"row_id": "r6", "predicted_label": "circle"},
    ]
    result = contracts.classification_metrics(dataset, splits["test"], rows)
    assert result == {
        "count": 2,
        "accuracy": 0.5,
        "macro_f1": 1 / 3,
        "confusion": [[0, 0, 0], [0, 1, 0], [1, 0, 0]],
        "label_order": ["circle", "square", "triangle"],
        "zero_division": 0,
    }


@pytest.mark.parametrize("change", ["id", "label", "fingerprint", "empty"])
def test_dataset_rejects_invalid_records(tiny_inputs: tuple[Path, Path, Path], change: str) -> None:
    value = json.loads(tiny_inputs[0].read_text())
    row = value["records"][1]
    if change == "id":
        row["row_id"] = "r1"
    elif change == "label":
        row["label"] = "unknown"
    elif change == "fingerprint":
        row["content_sha256"] = "0" * 64
    else:
        row["text"] = " "
    with pytest.raises(ValueError, match=r"row_id|label|sha256|text"):
        api("contracts").validate_dataset(value)


@pytest.mark.parametrize(
    "change", ["group", "duplicate", "missing", "extra", "empty", "normalized"]
)
def test_split_rejects_leakage_and_inexact_partition(
    tiny_inputs: tuple[Path, Path, Path], change: str
) -> None:
    contracts = api("contracts")
    data = json.loads(tiny_inputs[0].read_text())
    splits = json.loads(tiny_inputs[1].read_text())
    if change == "group":
        data["records"][3]["group_id"] = "r1"
    elif change == "normalized":
        data["records"][3]["text"] = " CIRCLE   RED "
        data["records"][3]["content_sha256"] = hashlib.sha256(b" CIRCLE   RED ").hexdigest()
    elif change == "duplicate":
        splits["test"].append("r1")
    elif change == "missing":
        splits["test"].pop()
    elif change == "extra":
        splits["test"].append("unknown")
    else:
        splits["validation"] = []
    dataset = contracts.validate_dataset(data)
    with pytest.raises(ValueError, match=r"split|partition|row_id"):
        contracts.validate_splits(splits, dataset)


@pytest.mark.parametrize("ids", [["r6", "r5"], ["r5"], ["r5", "r6", "r1"], ["r5", "r5"]])
def test_predictions_require_exact_frozen_order(
    tiny_inputs: tuple[Path, Path, Path], ids: list[str]
) -> None:
    contracts = api("contracts")
    dataset = contracts.validate_dataset(json.loads(tiny_inputs[0].read_text()))
    with pytest.raises(ValueError, match="prediction"):
        contracts.validate_predictions(
            [{"row_id": row, "predicted_label": "circle"} for row in ids], dataset, ("r5", "r6")
        )


def test_rule_bundle_predicts_and_is_immutable(
    rule_bundle: Path, tiny_inputs: tuple[Path, Path, Path]
) -> None:
    artifacts = api("artifacts")
    verified = verify(rule_bundle)
    assert verified.dataset.labels == ("circle", "square", "triangle")
    loaded = artifacts.load_trusted_local_classifier(
        rule_bundle, digest(rule_bundle / "manifest.json")
    )
    assert artifacts.predict_documents(loaded, ["SMALL  SQUARE", "blue triangle"]) == [
        "square",
        "circle",
    ]
    for bad in ([], [""], [" "], ["x" * 10001], [3]):
        with pytest.raises(ValueError, match="text"):
            artifacts.predict_documents(loaded, bad)
    before = (rule_bundle / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        artifacts.write_run_new(
            rule_bundle,
            data=tiny_inputs[0],
            splits=tiny_inputs[1],
            sources=tiny_inputs[2],
            model=b"",
            predictions=[],
            manifest={},
            measurement={},
            selection={},
        )
    assert (rule_bundle / "manifest.json").read_bytes() == before


def test_manifest_requires_external_digest_and_expected_dataset(rule_bundle: Path) -> None:
    artifacts = api("artifacts")
    with pytest.raises(ValueError, match="manifest"):
        artifacts.verify_bundle(rule_bundle, expected_manifest_sha256="0" * 64)
    with pytest.raises(ValueError, match="dataset_sha256"):
        artifacts.verify_bundle(
            rule_bundle,
            expected_manifest_sha256=digest(rule_bundle / "manifest.json"),
            dataset_sha256="0" * 64,
        )


@pytest.mark.parametrize("logical", ["data", "splits"])
def test_expected_identity_is_compared_to_actual_artifact_bytes(
    rule_bundle: Path, logical: str
) -> None:
    manifest = json.loads((rule_bundle / "manifest.json").read_text())
    original_dataset_sha = manifest["dataset_sha256"]
    original_split_sha = manifest["split_sha256"]
    path = rule_bundle / manifest["artifacts"][logical]["path"]
    value = json.loads(path.read_text())
    if logical == "data":
        value["records"][5]["text"] = "altered green triangle"
        value["records"][5]["content_sha256"] = hashlib.sha256(
            b"altered green triangle"
        ).hexdigest()
    else:
        value["train"].reverse()
    rewrite_artifact(rule_bundle, logical, value)
    with pytest.raises(ValueError, match="identity"):
        api("artifacts").verify_bundle(
            rule_bundle,
            expected_manifest_sha256=digest(rule_bundle / "manifest.json"),
            dataset_sha256=original_dataset_sha,
            split_sha256=original_split_sha,
        )


@pytest.mark.parametrize("logical", ["data", "model", "sources", "predictions", "metrics"])
def test_modified_bytes_fail_even_with_unchanged_report(rule_bundle: Path, logical: str) -> None:
    manifest = json.loads((rule_bundle / "manifest.json").read_text())
    (rule_bundle / manifest["artifacts"][logical]["path"]).write_bytes(b"tamper")
    with pytest.raises(ValueError, match="sha256"):
        verify(rule_bundle)


@pytest.mark.parametrize("path", ["../outside", "C:/model.pkl", "/tmp/model", "a\\b"])
def test_bad_artifact_paths_fail(rule_bundle: Path, path: str) -> None:
    manifest = json.loads((rule_bundle / "manifest.json").read_text())
    manifest["artifacts"]["model"]["path"] = path
    (rule_bundle / "manifest.json").write_bytes(encode(manifest))
    with pytest.raises(ValueError, match="path"):
        verify(rule_bundle)


@pytest.mark.parametrize(
    "logical", ["metrics", "predictions", "errors", "measurement", "selection"]
)
def test_semantic_corruption_fails_after_rehash(rule_bundle: Path, logical: str) -> None:
    bad: object = (
        {"count": 999}
        if logical != "predictions"
        else [{"row_id": "r6", "predicted_label": "square"}]
    )
    rewrite_artifact(rule_bundle, logical, bad)
    with pytest.raises(ValueError, match=r"metrics|predictions|errors|timings|selection"):
        verify(rule_bundle)


@pytest.mark.parametrize(
    "change", ["format", "labels", "preprocessing", "schema", "model-labels", "size", "source"]
)
def test_unsupported_contract_or_label_mapping_fails(rule_bundle: Path, change: str) -> None:
    manifest = json.loads((rule_bundle / "manifest.json").read_text())
    if change == "format":
        manifest["model"]["format"] = "remote-pickle"
    elif change == "labels":
        manifest["labels"].reverse()
    elif change == "preprocessing":
        manifest["preprocessing"]["version"] = 99
    elif change == "schema":
        manifest["schema_version"] = 99
    elif change == "size":
        manifest["artifacts"]["model"]["size_bytes"] = 0
    elif change == "source":
        rewrite_artifact(
            rule_bundle, "sources", {"schema_version": 1, "sources": [], "annotation_policy": "x"}
        )
        with pytest.raises(ValueError, match="sources"):
            verify(rule_bundle)
        return
    else:
        model = json.loads((rule_bundle / "model.json").read_text())
        model["labels"].reverse()
        rewrite_artifact(rule_bundle, "model", model)
        with pytest.raises(ValueError, match="label"):
            api("artifacts").load_trusted_local_classifier(
                rule_bundle, digest(rule_bundle / "manifest.json")
            )
        return
    (rule_bundle / "manifest.json").write_bytes(encode(manifest))
    with pytest.raises(ValueError, match=r"format|label|preprocessing|schema|size"):
        verify(rule_bundle)


@pytest.mark.parametrize("version", [True, 1.0])
def test_preprocessing_version_requires_integer_type(rule_bundle: Path, version: object) -> None:
    manifest_path = rule_bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["preprocessing"]["version"] = version
    manifest_path.write_bytes(encode(manifest))
    with pytest.raises(ValueError, match="preprocessing"):
        api("artifacts").load_trusted_local_classifier(rule_bundle, digest(manifest_path))


def test_teacher_comparison_reloads_in_fresh_process_after_move(tmp_path: Path) -> None:
    demo = api("part_a1.demo")
    output = demo.run_demo(tmp_path / "original")
    moved = tmp_path / "fresh"
    shutil.move(str(output), moved)
    comparison = json.loads((moved / "comparison.json").read_text())
    assert comparison["selection"]["frozen_before_test"] is True
    assert set(comparison["methods"]) == {"rules", "tfidf-linear"}
    for method in ("rules", "tfidf-linear"):
        bundle = moved / method
        verify(bundle)
        manifest_sha = digest(bundle / "manifest.json")
        script = """import json,sys
from pathlib import Path
from projects.document_intelligence_lab.artifacts import (
    load_trusted_local_classifier,predict_documents)
root=Path(sys.argv[1])
model=load_trusted_local_classifier(root,sys.argv[2],trusted_local_artifact=True)
data=json.loads((root/'data.json').read_text())
ids=json.loads((root/'splits.json').read_text())['test']
texts={r['row_id']:r['text'] for r in data['records']}
print(json.dumps(predict_documents(model,[texts[i] for i in ids])))
"""
        result = subprocess.run(
            [sys.executable, "-c", script, str(bundle), manifest_sha],
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        saved = json.loads((bundle / "predictions.json").read_text())
        assert json.loads(result.stdout) == [row["predicted_label"] for row in saved]
        if method == "tfidf-linear":
            with pytest.raises(ValueError, match="trusted"):
                api("artifacts").load_trusted_local_classifier(bundle, manifest_sha)
            manifest = json.loads((bundle / "manifest.json").read_text())
            manifest["versions"]["sklearn"] = "0.0.incompatible"
            (bundle / "manifest.json").write_bytes(encode(manifest))
            with pytest.raises(ValueError, match="version"):
                api("artifacts").load_trusted_local_classifier(
                    bundle, digest(bundle / "manifest.json"), trusted_local_artifact=True
                )


def test_prediction_truth_column_cannot_override_data(tiny_inputs: tuple[Path, Path, Path]) -> None:
    contracts = api("contracts")
    dataset = contracts.validate_dataset(json.loads(tiny_inputs[0].read_text()))
    with pytest.raises(ValueError, match="truth"):
        contracts.validate_predictions(
            [{"row_id": "r5", "predicted_label": "square", "truth": "circle"}], dataset, ("r5",)
        )


def test_writer_rejects_bad_identity_before_creating_output(
    tmp_path: Path, tiny_inputs: tuple[Path, Path, Path]
) -> None:
    with pytest.raises(ValueError, match="predictions"):
        api("artifacts").write_run_new(
            tmp_path / "bad",
            data=tiny_inputs[0],
            splits=tiny_inputs[1],
            sources=tiny_inputs[2],
            model=b"{}",
            predictions=[],
            manifest={},
            measurement={},
            selection={},
        )
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("logical", ["metrics", "model", "sources"])
def test_boolean_cannot_substitute_for_schema_or_count(rule_bundle: Path, logical: str) -> None:
    manifest = json.loads((rule_bundle / "manifest.json").read_text())
    value = json.loads((rule_bundle / manifest["artifacts"][logical]["path"]).read_text())
    if logical == "metrics":
        value["confusion"][0][0] = False
    else:
        value["schema_version"] = True
    rewrite_artifact(rule_bundle, logical, value)
    with pytest.raises(ValueError, match=r"schema|metrics"):
        verify(rule_bundle)


@pytest.mark.parametrize("field", ["condition", "format"])
def test_malformed_fields_raise_contract_error(rule_bundle: Path, field: str) -> None:
    if field == "condition":
        value = json.loads((rule_bundle / "measurement.json").read_text())
        value["timings"][0][field] = []
        rewrite_artifact(rule_bundle, "measurement", value)
    else:
        manifest = json.loads((rule_bundle / "manifest.json").read_text())
        manifest["model"][field] = []
        (rule_bundle / "manifest.json").write_bytes(encode(manifest))
    with pytest.raises(ValueError, match=r"condition|format"):
        verify(rule_bundle)


def test_contract_objects_do_not_mutate_input(tiny_inputs: tuple[Path, Path, Path]) -> None:
    contracts = api("contracts")
    raw = json.loads(tiny_inputs[0].read_text())
    before = copy.deepcopy(raw)
    dataset = contracts.validate_dataset(raw)
    assert raw == before
    with pytest.raises((AttributeError, TypeError)):
        dataset.records[0].label = "square"


def test_teacher_known_errors_and_train_only_fitted_idf(tmp_path: Path) -> None:
    artifacts = api("artifacts")
    output = api("part_a1.demo").run_demo(tmp_path / "run")
    rules = json.loads((output / "rules" / "metrics.json").read_text())
    assert rules["confusion"] == [[2, 0, 0], [0, 2, 0], [2, 0, 0]]
    assert rules["accuracy"] == pytest.approx(2 / 3)
    assert rules["macro_f1"] == pytest.approx(5 / 9)
    errors = json.loads((output / "rules" / "errors.json").read_text())
    assert [row["row_id"] for row in errors] == ["s18", "s21"]
    measurement = json.loads((output / "tfidf-linear" / "measurement.json").read_text())
    assert [
        (row["name"], row["condition"], row["sample_count"]) for row in measurement["timings"]
    ] == [
        ("test_inference", "warm", 6),
        ("fit", "cold", 12),
    ]
    model = artifacts.load_trusted_local_classifier(
        output / "tfidf-linear",
        digest(output / "tfidf-linear" / "manifest.json"),
        trusted_local_artifact=True,
    ).model
    vectorizer = model.named_steps["tfidf"]
    # 12 train documents, exactly six contain object. Validation/test never fit IDF.
    assert vectorizer.idf_[vectorizer.vocabulary_["object"]] == pytest.approx(math.log(13 / 7) + 1)


@pytest.mark.parametrize("flag", [False, 1, "true", None])
def test_pickle_load_requires_literal_operator_trust(
    tmp_path: Path, flag: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = api("part_a1.demo").run_demo(tmp_path / "run") / "tfidf-linear"

    def forbidden(payload: bytes) -> None:
        raise AssertionError("deserialization happened before explicit trust")

    monkeypatch.setattr("pickle.loads", forbidden)
    with pytest.raises(ValueError, match="trusted"):
        api("artifacts").load_trusted_local_classifier(
            root, digest(root / "manifest.json"), trusted_local_artifact=flag
        )
