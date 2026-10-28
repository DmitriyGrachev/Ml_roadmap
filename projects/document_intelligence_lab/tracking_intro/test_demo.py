"""Base checks never pretend that a fake tracker is an MLflow integration."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from types import ModuleType

import pytest


def test_local_runtime_disables_telemetry_before_import(monkeypatch: pytest.MonkeyPatch) -> None:
    from .demo import _mlflow

    monkeypatch.setenv("MLFLOW_DISABLE_TELEMETRY", "false")
    observed = []

    def observe_import(name: str, package: str | None = None) -> ModuleType:
        observed.append(os.environ.get("MLFLOW_DISABLE_TELEMETRY"))
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(importlib, "import_module", observe_import)
    with pytest.raises(RuntimeError, match="NOT_RUN"):
        _mlflow()
    assert observed == ["true"]


def test_local_store_paths_reject_relative_or_remote_selection(tmp_path: Path) -> None:
    from .demo import local_store

    uri, artifacts = local_store(tmp_path / "runs.sqlite", tmp_path / "artifacts")
    assert uri.startswith("sqlite:///")
    assert str(tmp_path / "runs.sqlite").replace("\\", "/") in uri
    assert artifacts == (tmp_path / "artifacts").as_uri()
    with pytest.raises(ValueError, match="absolute"):
        local_store(Path("relative.sqlite"), tmp_path / "artifacts")
    with pytest.raises(ValueError, match="local"):
        local_store(Path("//server/share/runs.sqlite"), tmp_path / "artifacts")


def test_missing_mlflow_is_explicit_not_run_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from .demo import run_demo

    real_import = importlib.import_module

    def no_mlflow(name: str, package: str | None = None) -> ModuleType:
        if name == "mlflow":
            raise ModuleNotFoundError("mlflow")
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", no_mlflow)
    with pytest.raises(RuntimeError, match=r"NOT_RUN.*MLflow"):
        run_demo(tmp_path / "tracking")
    assert not (tmp_path / "tracking").exists()


def test_cli_missing_runtime_has_concise_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from .demo import main

    real_import = importlib.import_module

    def no_mlflow(name: str, package: str | None = None) -> ModuleType:
        if name == "mlflow":
            raise ModuleNotFoundError("mlflow")
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", no_mlflow)
    with pytest.raises(SystemExit) as error:
        main(["--output", str(tmp_path / "tracking")])
    assert error.value.code == 2
    assert "NOT_RUN: MLflow runtime missing" in capsys.readouterr().err
    assert not (tmp_path / "tracking").exists()


@pytest.mark.parametrize(
    "uri", ["https://example.com/weights", "s3://bucket/model", "file:///outside/weights"]
)
def test_restore_refuses_nonlocal_or_outside_artifact_metadata(tmp_path: Path, uri: str) -> None:
    from .demo import require_local_artifact_uri

    with pytest.raises(ValueError, match="local artifact root"):
        require_local_artifact_uri(uri, tmp_path / "artifacts")


def test_restore_accepts_only_selected_root(tmp_path: Path) -> None:
    from .demo import require_local_artifact_uri

    root = tmp_path / "artifacts"
    require_local_artifact_uri((root / "run" / "artifacts").as_uri(), root)
