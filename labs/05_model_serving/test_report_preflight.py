"""Raw-report arithmetic and fail-closed local asset inventory, all offline."""

import importlib
import json
from pathlib import Path

import pytest


def test_summary_is_derived_from_labelled_raw_records() -> None:
    report = importlib.import_module("labs.05_model_serving.experiments.report")
    raw = [
        {"status": "ok", "completion_tokens": 4},
        {"status": "deadline", "completion_tokens": None},
        {"status": "ok", "completion_tokens": 6},
    ]
    summary = report.summarize(raw, elapsed_s=2.0, evidence="synthetic")
    assert summary == {
        "evidence": "synthetic",
        "requests": 3,
        "completed": 2,
        "errors": 1,
        "completed_requests_per_s": 1.0,
        "completed_output_tokens_per_s": 5.0,
    }
    assert json.loads(json.dumps({"raw": raw, "summary": summary}))["raw"] == raw


@pytest.mark.parametrize("elapsed", [0.0, -1.0, float("nan")])
def test_summary_rejects_impossible_elapsed(elapsed: float) -> None:
    report = importlib.import_module("labs.05_model_serving.experiments.report")
    with pytest.raises(ValueError, match="elapsed"):
        report.summarize([], elapsed_s=elapsed, evidence="synthetic")


def test_missing_server_usage_stays_unknown() -> None:
    report = importlib.import_module("labs.05_model_serving.experiments.report")
    assert (
        report.summarize(
            [{"status": "ok", "completion_tokens": None}], elapsed_s=1, evidence="live_endpoint"
        )["completed_output_tokens_per_s"]
        is None
    )
    with pytest.raises(ValueError, match="evidence"):
        report.summarize([], elapsed_s=1, evidence="benchmark")


def test_asset_inventory_checks_content_size_and_path_escape(tmp_path: Path) -> None:
    preflight = importlib.import_module("labs.05_model_serving.environment.preflight")
    asset = tmp_path / "config.json"
    asset.write_bytes(b"{}")
    inventory = [
        {
            "path": "config.json",
            "bytes": 2,
            "sha256": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
        }
    ]
    preflight.verify_files(tmp_path, inventory)
    asset.write_bytes(b"[]")
    with pytest.raises(ValueError, match="hash"):
        preflight.verify_files(tmp_path, inventory)
    with pytest.raises(ValueError, match="path"):
        preflight.verify_files(tmp_path, [{**inventory[0], "path": "../config.json"}])
    with pytest.raises(ValueError, match="size"):
        preflight.verify_files(tmp_path, [{**inventory[0], "bytes": 3}])
    with pytest.raises(ValueError, match="inventory"):
        preflight.verify_files(tmp_path, [])


def test_preflight_windows_exits_without_importing_gpu_runtime(tmp_path: Path) -> None:
    preflight = importlib.import_module("labs.05_model_serving.environment.preflight")
    assert preflight.check(tmp_path / "absent.json", system="Windows") == [
        "NOT_RUN: Linux required; Windows environments are not modified"
    ]


def test_preflight_linux_missing_assets_are_not_ready(tmp_path: Path) -> None:
    preflight = importlib.import_module("labs.05_model_serving.environment.preflight")
    assert preflight.check(tmp_path / "absent.json", system="Linux") == [
        "NOT_RUN: missing or inconsistent manifest/runtime/assets; review local inventory"
    ]
