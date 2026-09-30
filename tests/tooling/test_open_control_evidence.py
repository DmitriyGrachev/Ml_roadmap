"""Byte/identity composition on unrelated two-file hand examples."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest


def _bundle(root: Path) -> dict[str, object]:
    blobs = {
        "input.txt": b"toy input",
        "split.json": b'["toy"]',
        "outputs.json": b'[{"id":"toy"}]',
        "report.md": b"draft",
        "implementation.txt": b"untrusted text, never executed",
    }
    for name, content in blobs.items():
        (root / name).write_bytes(content)
    manifest: dict[str, object] = {
        "schema_version": 1,
        "exercise_id": "toy-control",
        "run_id": "toy-run",
        "dataset_sha256": hashlib.sha256(blobs["input.txt"]).hexdigest(),
        "split_sha256": hashlib.sha256(blobs["split.json"]).hexdigest(),
        "config": {},
        "artifacts": {name: hashlib.sha256(content).hexdigest() for name, content in blobs.items()},
        "review_status": "REQUIRES_REVIEW",
    }
    (root / "manifest.json").write_text(json.dumps(manifest))
    return manifest


def test_bundle_binds_actual_bytes_and_identity(tmp_path: Path) -> None:
    module = importlib.import_module("roadmap_tools.open_control_evidence")
    _bundle(tmp_path)
    result = module.load_bundle(tmp_path, "toy-control", {"input.txt": b"toy input"})
    assert result["run_id"] == "toy-run"


@pytest.mark.parametrize(
    "mutation",
    ["missing", "corrupt", "foreign", "stale", "review", "split", "empty_report", "path"],
)
def test_bundle_rejects_invalid_evidence(tmp_path: Path, mutation: str) -> None:
    module = importlib.import_module("roadmap_tools.open_control_evidence")
    manifest = _bundle(tmp_path)
    artifacts = dict(manifest["artifacts"])  # type: ignore[call-overload]
    if mutation == "missing":
        artifacts.pop("outputs.json")
    elif mutation == "corrupt":
        (tmp_path / "outputs.json").write_bytes(b"different")
    elif mutation == "foreign":
        manifest["exercise_id"] = "elsewhere"
    elif mutation == "stale":
        (tmp_path / "input.txt").write_bytes(b"previous input")
        artifacts["input.txt"] = hashlib.sha256(b"previous input").hexdigest()
        manifest["dataset_sha256"] = artifacts["input.txt"]
    elif mutation == "review":
        manifest["review_status"] = "PASSED"
    elif mutation == "split":
        manifest["split_sha256"] = "0" * 64
    elif mutation == "empty_report":
        (tmp_path / "report.md").write_bytes(b"")
        artifacts["report.md"] = hashlib.sha256(b"").hexdigest()
    else:
        artifacts["../elsewhere"] = "0" * 64
    manifest["artifacts"] = artifacts
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=r"missing|differs|does not match|review|empty|relative"):
        module.load_bundle(tmp_path, "toy-control", {"input.txt": b"toy input"})
