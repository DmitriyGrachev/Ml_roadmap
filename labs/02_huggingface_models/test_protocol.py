"""Validate real local artifact bytes and recomputed results, without downloads."""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


def protocol() -> Any:
    assert Path(__file__).with_name("protocol.py").is_file(), "artifact protocol is missing"
    return importlib.import_module("labs.02_huggingface_models.protocol")


def test_checksum_rejects_changed_snapshot_and_size(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.csv"
    snapshot.write_bytes(b"text,label\nhello,0\n")
    digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    assert protocol().verify_file(snapshot, digest, 19) == digest
    snapshot.write_bytes(b"text,label\nother,0\n")
    with pytest.raises(ValueError, match="checksum"):
        protocol().verify_file(snapshot, digest, 19)
    with pytest.raises(ValueError, match="size"):
        protocol().verify_file(snapshot, digest, 20)


def test_report_rejects_missing_artifact_and_mock_quality(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="report"):
        protocol().validate_offline_artifacts(tmp_path)
    (tmp_path / "offline-report.json").write_text(
        json.dumps({"schema_version": 1, "evidence": "LIVE_VERIFIED"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="evidence"):
        protocol().validate_offline_artifacts(tmp_path)


def test_safe_artifact_path_rejects_escape_and_missing_file(tmp_path: Path) -> None:
    for name in ("../outside.json", "C:/outside.json", "/outside.json", "missing.json"):
        with pytest.raises(ValueError, match="artifact"):
            protocol().artifact_path(tmp_path, name)


def test_comparison_recomputes_metrics() -> None:
    reports = {
        name: {
            "predictions": [0, 2, 2, 3],
            "accuracy": 0.75,
            "macro_f1": 2 / 3,
            "warm_seconds": 0.1,
            "peak_memory_bytes": None,
            "memory_note": "NOT_MEASURED: portable process monitor unavailable",
        }
        for name in ("tfidf_linear", "frozen_embeddings", "adapted_encoder")
    }
    module = protocol()
    module.validate_comparison(reports, [0, 1, 2, 3])
    reports["tfidf_linear"]["accuracy"] = 0.99
    with pytest.raises(ValueError, match="computed"):
        module.validate_comparison(reports, [0, 1, 2, 3])


def test_resource_download_reuses_verified_file_and_never_fetches_unknown_names(
    tmp_path: Path,
) -> None:
    assert Path(__file__).with_name("download.py").is_file(), "download entry point is missing"
    module = importlib.import_module("labs.02_huggingface_models.download")
    calls: list[str] = []
    data = b"local snapshot"

    def fetch(url: str, destination: Path) -> None:
        calls.append(url)
        destination.write_bytes(data)

    spec = {
        "filename": "config.json",
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
    }
    module.fetch_verified("https://huggingface.co/test/resolve/rev", spec, tmp_path, fetch)
    module.fetch_verified("https://huggingface.co/test/resolve/rev", spec, tmp_path, fetch)
    assert len(calls) == 1
    assert (tmp_path / "config.json").read_bytes() == data
    with pytest.raises(ValueError, match="filename"):
        module.fetch_verified(
            "https://huggingface.co/test", {**spec, "filename": "../x"}, tmp_path, fetch
        )


@pytest.fixture
def offline_report(tmp_path: Path) -> Path:
    torch = pytest.importorskip("torch", reason="NOT_RUN: install the opt-in training group")
    pytest.importorskip("transformers", reason="NOT_RUN: install the opt-in training group")
    from sklearn.metrics import accuracy_score, f1_score

    example = importlib.import_module("labs.02_huggingface_models.example")
    model, tokenizer = example.make_local_components(num_labels=4)
    model.save_pretrained(tmp_path / "checkpoint", safe_serialization=True)
    tokenizer.save_pretrained(tmp_path / "checkpoint")
    # These are test-only records, not a completed learner report.
    data = {
        "records": [
            {"row_id": name, "text": text, "label": label}
            for name, text, label in (
                ("a", "red", 0),
                ("b", "blue", 1),
                ("c", "red square", 0),
                ("d", "blue circle", 1),
            )
        ]
    }
    splits = {"train": ["a"], "validation": ["b"], "test": ["c", "d"]}
    (tmp_path / "data.json").write_text(json.dumps(data), encoding="utf-8")
    (tmp_path / "splits.json").write_text(json.dumps(splits), encoding="utf-8")
    model.eval()
    with torch.inference_mode():
        predictions = (
            model(
                **tokenizer(
                    ["red square", "blue circle"],
                    padding=True,
                    truncation=True,
                    max_length=8,
                    return_tensors="pt",
                )
            )
            .logits.argmax(dim=1)
            .tolist()
        )
    labels = [0, 1]
    report = {
        "schema_version": 1,
        "evidence": "LOCAL_RANDOM_ENCODER_STUDENT_RUN",
        "pretrained_quality": "NOT_RUN",
        "seed": 17,
        "code_revision": "1" * 40,
        "model": {"id": "local-random-bert", "revision": "fixture-v1"},
        "data": {
            "path": "data.json",
            "sha256": hashlib.sha256((tmp_path / "data.json").read_bytes()).hexdigest(),
        },
        "splits": {
            "path": "splits.json",
            "sha256": hashlib.sha256((tmp_path / "splits.json").read_bytes()).hexdigest(),
        },
        "checkpoint_files": {
            path.relative_to(tmp_path).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (tmp_path / "checkpoint").iterdir()
            if path.is_file()
        },
        "test_ids": ["c", "d"],
        "labels": labels,
        "predictions": predictions,
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(
            f1_score(labels, predictions, labels=[0, 1, 2, 3], average="macro", zero_division=0)
        ),
        "config": {
            "batch_size": 2,
            "max_length": 8,
            "max_steps": 2,
            "learning_rate": 2e-5,
            "preprocessing": "nfkc-casefold-space-v1",
        },
        "versions": {
            name: "test-fixture"
            for name in ("python", "torch", "transformers", "datasets", "scikit_learn")
        },
    }
    (tmp_path / "offline-report.json").write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "analysis.md").write_text(
        "Test-only evidence: a temporary randomly initialized model produces finite predictions. "
        "The labels are invented and the sample is extremely small. These measured outputs check "
        "serialization and inference mechanics; they provide no evidence about customer-support "
        "classification quality, generalization or safe production use.",
        encoding="utf-8",
    )
    return tmp_path


def test_offline_report_checks_real_checkpoint_predictions(offline_report: Path) -> None:
    root = offline_report
    module = protocol()
    assert module.validate_offline_artifacts(root)["evidence"] == "LOCAL_RANDOM_ENCODER_STUDENT_RUN"
    report = json.loads((root / "offline-report.json").read_text(encoding="utf-8"))
    report["predictions"] = [(value + 1) % 4 for value in report["predictions"]]
    from sklearn.metrics import accuracy_score, f1_score

    report["accuracy"] = float(accuracy_score(report["labels"], report["predictions"]))
    report["macro_f1"] = float(
        f1_score(
            report["labels"],
            report["predictions"],
            labels=[0, 1, 2, 3],
            average="macro",
            zero_division=0,
        )
    )
    (root / "offline-report.json").write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="checkpoint predictions"):
        module.validate_offline_artifacts(root)


def test_offline_report_rejects_split_overlap(offline_report: Path) -> None:
    root = offline_report
    path = root / "splits.json"
    splits = json.loads(path.read_text(encoding="utf-8"))
    splits["train"].append("c")
    path.write_text(json.dumps(splits), encoding="utf-8")
    report = json.loads((root / "offline-report.json").read_text(encoding="utf-8"))
    report["splits"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (root / "offline-report.json").write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="overlap"):
        protocol().validate_offline_artifacts(root)


def test_offline_report_requires_code_revision(offline_report: Path) -> None:
    path = offline_report / "offline-report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    report.pop("code_revision")
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="code_revision"):
        protocol().validate_offline_artifacts(offline_report)


@pytest.mark.parametrize("value", [None, 0, -0.1, True, float("nan"), float("inf")])
def test_offline_report_rejects_missing_or_invalid_learning_rate(
    offline_report: Path, value: object
) -> None:
    path = offline_report / "offline-report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if value is None:
        report["config"].pop("learning_rate")
    else:
        report["config"]["learning_rate"] = value
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="learning_rate"):
        protocol().validate_offline_artifacts(offline_report)


@pytest.mark.parametrize("value", [None, "unsupported", "", 3])
def test_offline_report_requires_supported_preprocessing(
    offline_report: Path, value: object
) -> None:
    path = offline_report / "offline-report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if value is None:
        report["config"].pop("preprocessing")
    else:
        report["config"]["preprocessing"] = value
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="preprocessing"):
        protocol().validate_offline_artifacts(offline_report)


def test_real_runner_rejects_predictions_unrelated_to_saved_checkpoint(
    offline_report: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shutil

    from sklearn.metrics import accuracy_score, f1_score

    runner = importlib.import_module("labs.02_huggingface_models.run")
    starter = importlib.import_module("labs.02_huggingface_models.starter")
    report = json.loads((offline_report / "offline-report.json").read_text(encoding="utf-8"))
    data = json.loads((offline_report / "data.json").read_text(encoding="utf-8"))
    records = [starter.Document(**record) for record in data["records"]]
    cache = tmp_path / "cache"
    (cache / "dataset").mkdir(parents=True)
    (cache / "dataset" / "local.csv").write_text(
        "instruction,intent\nred,create_account\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        runner,
        "verify_cache",
        lambda _: {"dataset": {"files": [{"filename": "local.csv"}]}, "model": {"id": "test-only"}},
    )
    monkeypatch.setattr(
        runner,
        "prepare_splits",
        lambda rows, seed: {"train": records[:1], "validation": records[1:2], "test": records[2:]},
    )

    def counterfeit(source: Path, splits: Any, config: Any, output: Path) -> dict[str, Any]:
        shutil.copytree(offline_report / "checkpoint", output)
        predictions = [(value + 1) % 4 for value in report["predictions"]]
        labels = report["labels"]
        return {
            name: {
                "predictions": predictions,
                "accuracy": float(accuracy_score(labels, predictions)),
                "macro_f1": float(
                    f1_score(
                        labels, predictions, labels=[0, 1, 2, 3], average="macro", zero_division=0
                    )
                ),
                "warm_seconds": 0.01,
                "peak_memory_bytes": None,
                "memory_note": "NOT_MEASURED: adversarial fixture",
            }
            for name in ("tfidf_linear", "frozen_embeddings", "adapted_encoder")
        }

    monkeypatch.setattr(runner, "compare_models", counterfeit)
    with pytest.raises(ValueError, match="checkpoint predictions"):
        runner.run_real(
            cache,
            tmp_path / "real-output",
            starter.RunConfig(batch_size=2, max_length=8, max_steps=2),
        )
