"""Report protocol checks do not require PyTorch or a model download."""

import hashlib
import json
import os
from importlib import import_module
from pathlib import Path

import pytest

report = import_module("labs.01_pytorch_foundations.report")


def valid_report(checkpoint: Path) -> dict[str, object]:
    checkpoint.write_bytes(b"local fixture checkpoint")
    dataset = checkpoint.with_name("observations.csv")
    dataset.write_bytes(b"id,width,label\nobj-1,2,0\nobj-2,3,1\nobj-3,4,0\nobj-4,5,1\n")
    return {
        "schema_version": 1,
        "task": "object-features-v1",
        "seed": 23,
        "dataset": str(dataset),
        "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "code_revision": "working-tree (dirty)",
        "config": {
            "batch_size": 2,
            "learning_rate": 0.1,
            "epochs": 2,
            "device": "cpu",
            "input_dim": 2,
            "n_classes": 2,
            "optimizer": "SGD",
            "momentum": 0.9,
        },
        "train_ids": ["obj-1", "obj-2"],
        "validation_ids": ["obj-3", "obj-4"],
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "versions": {"python": "3.12.0", "torch": "2.0.0"},
        "labels": [0, 1],
        "predictions": [0, 0],
        "metrics": {"count": 2, "accuracy": 0.5},
        "analysis": {
            "error_pattern": (
                "The second object was confused with the first class; inspect its features."
            ),
            "next_experiment": (
                "Try more diverse examples for the second class and compare by split."
            ),
        },
    }


def test_report_accepts_traceable_computed_results(tmp_path: Path) -> None:
    payload = valid_report(tmp_path / "checkpoint.pt")
    path = tmp_path / "report.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert report.validate_report(path) == payload


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_metric",
        "overlap",
        "missing_checkpoint",
        "placeholder",
        "dataset_hash",
        "missing_dataset",
        "bad_config",
        "missing_revision",
        "out_of_range_label",
        "out_of_range_prediction",
    ],
)
def test_report_rejects_unverifiable_submission(tmp_path: Path, mutation: str) -> None:
    payload = valid_report(tmp_path / "checkpoint.pt")
    if mutation == "wrong_metric":
        payload["metrics"] = {"count": 2, "accuracy": 0.9}
    elif mutation == "overlap":
        payload["validation_ids"] = ["obj-2", "obj-4"]
    elif mutation == "missing_checkpoint":
        payload["checkpoint"] = str(tmp_path / "missing.pt")
    elif mutation == "dataset_hash":
        payload["dataset_sha256"] = "a" * 64
    elif mutation == "missing_dataset":
        payload["dataset"] = str(tmp_path / "missing.csv")
    elif mutation == "bad_config":
        payload["config"] = {
            "batch_size": 0,
            "learning_rate": 0.1,
            "epochs": 2,
            "device": "cpu",
            "input_dim": 2,
            "n_classes": 2,
            "optimizer": "SGD",
            "momentum": 0.9,
        }
    elif mutation == "missing_revision":
        payload["code_revision"] = "unknown"
    elif mutation == "out_of_range_label":
        payload["labels"] = [0, 2]
    elif mutation == "out_of_range_prediction":
        payload["predictions"] = [0, 2]
    else:
        payload["analysis"] = {"error_pattern": "TODO", "next_experiment": "TBD"}
    path = tmp_path / "report.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(
        ValueError, match=r"accuracy|overlap|checkpoint|placeholder|dataset|config|revision|class"
    ):
        report.validate_report(path)


def test_relative_artifact_paths_are_resolved_from_repository_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = valid_report(tmp_path / "checkpoint.pt")
    repository_root = Path(__file__).resolve().parents[2]
    payload["dataset"] = os.path.relpath(str(payload["dataset"]), repository_root)
    payload["checkpoint"] = os.path.relpath(str(payload["checkpoint"]), repository_root)
    path = tmp_path / "report.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert report.validate_report(path) == payload


def test_student_report_is_present_and_valid() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    path = repository_root / "generated-reports/pytorch/report.json"
    if not path.exists():
        pytest.xfail("Learner report is not submitted under generated-reports/pytorch/")
    payload = report.validate_report(path)
    output_root = repository_root / "generated-reports/pytorch"
    assert (repository_root / payload["checkpoint"]).resolve().is_relative_to(output_root)
    assert (repository_root / payload["dataset"]).resolve().is_relative_to(output_root)
