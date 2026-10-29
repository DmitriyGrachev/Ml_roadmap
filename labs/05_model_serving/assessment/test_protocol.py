"""Synthetic contract fixtures do not count as a real serving experiment."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

protocol = importlib.import_module("labs.05_model_serving.assessment.protocol")
summary = importlib.import_module("labs.05_model_serving.experiments.report").summarize


def run_fixture() -> dict[str, Any]:
    raw = [
        {
            "request_index": 0,
            "status": "ok",
            "queue_ms": 0,
            "e2e_ms": 100,
            "ttft_ms": 20,
            "completion_tokens": 4,
        },
        {
            "request_index": 1,
            "status": "ok",
            "queue_ms": 0,
            "e2e_ms": 200,
            "ttft_ms": 40,
            "completion_tokens": 6,
        },
    ]
    return {
        "schema_version": 1,
        "evidence": "live_endpoint",
        "model_server_id": "fixture-model",
        "runtime_and_model": {
            "server_model_id": "fixture-model",
            "model_revision": "a" * 40,
            "runtime_versions": {"vllm": "fixture-only"},
        },
        "state": "warm",
        "concurrency": 1,
        "request_config": {"max_tokens": 128, "deadline_s": 30, "attempts_per_request": 1},
        "run_elapsed_s": 0.5,
        "raw": raw,
        "summary": summary(raw, elapsed_s=0.5, evidence="live_endpoint"),
    }


def bundle(directory: Path) -> dict[str, Any]:
    payloads = {
        "initial": json.dumps(run_fixture()),
        "restarted": json.dumps(run_fixture()),
        "environment": json.dumps(
            {
                "system": "Linux",
                "gpu": "synthetic fixture",
                "driver": "fixture-only",
                "vllm": "fixture-only",
            }
        ),
        "lock": "# synthetic lock fixture; not a runnable environment\n",
        "server_log": "synthetic startup/abort/restart log, only protocol fixture\n",
        "defense": "synthetic explanatory fixture; not learner evidence\n",
    }
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "status": "RECORDED_REQUIRES_REVIEW",
        "provider": "vllm",
        "model_repo": "fixture/model",
        "model_revision": "a" * 40,
        "server_model_id": "fixture-model",
        "server_command": ["vllm", "serve", "LOCAL_SNAPSHOT"],
        "artifacts": {},
    }
    for role, payload in payloads.items():
        path = directory / f"{role}.txt"
        path.write_text(payload, encoding="utf-8")
        manifest["artifacts"][role] = {
            "path": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    (directory / "evidence.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


def test_consistent_endpoint_report_keeps_raw_values() -> None:
    report = run_fixture()
    before = copy.deepcopy(report)
    result = protocol.validate_run(report)
    assert result == report
    assert report == before


@pytest.mark.parametrize("case", ["synthetic", "summary", "nan", "ttft", "ids", "wall", "bool"])
def test_run_rejects_inconsistent_measurements(case: str) -> None:
    report = run_fixture()
    if case == "synthetic":
        report["evidence"] = "synthetic"
    elif case == "summary":
        report["summary"]["completed"] = 999
    elif case == "nan":
        report["raw"][0]["e2e_ms"] = float("nan")
    elif case == "ttft":
        report["raw"][0]["ttft_ms"] = 101
    elif case == "ids":
        report["raw"][1]["request_index"] = 0
    elif case == "wall":
        report["run_elapsed_s"] = 0.01
    else:
        report["raw"][0]["completion_tokens"] = True
    with pytest.raises(
        ValueError,
        match=r"live_endpoint|summary|e2e_ms|ttft_ms|request_index|wall time|completion_tokens",
    ):
        protocol.validate_run(report)


def test_bundle_checks_artifact_bytes_and_cross_run_identity(tmp_path: Path) -> None:
    manifest = bundle(tmp_path)
    result = protocol.load_evidence(tmp_path)
    assert result["manifest"] == manifest
    assert result["review"] == "REQUIRES_REVIEW"
    (tmp_path / "lock.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        protocol.load_evidence(tmp_path)


@pytest.mark.parametrize(
    "case", ["not_run", "provider", "escape", "identity", "duplicate", "large", "non_text"]
)
def test_bundle_rejects_missing_false_or_unbounded_evidence(tmp_path: Path, case: str) -> None:
    manifest = bundle(tmp_path)
    if case == "not_run":
        manifest["status"] = "NOT_RUN"
    elif case == "provider":
        manifest["provider"] = "ollama"
    elif case == "escape":
        manifest["artifacts"]["lock"]["path"] = "../outside.txt"
    elif case == "duplicate":
        manifest["artifacts"]["restarted"] = manifest["artifacts"]["initial"]
    elif case == "large":
        (tmp_path / "server_log.txt").write_bytes(b"x" * 1_048_577)
    elif case == "non_text":
        payload = b"\xff\xfe"
        (tmp_path / "server_log.txt").write_bytes(payload)
        manifest["artifacts"]["server_log"]["sha256"] = hashlib.sha256(payload).hexdigest()
    else:
        changed = run_fixture()
        changed["runtime_and_model"]["model_revision"] = "b" * 40
        path = tmp_path / "restarted.txt"
        path.write_text(json.dumps(changed), encoding="utf-8")
        manifest["artifacts"]["restarted"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path / "evidence.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match=r"vLLM|path|identity|distinct|size|UTF-8"):
        protocol.load_evidence(tmp_path)
