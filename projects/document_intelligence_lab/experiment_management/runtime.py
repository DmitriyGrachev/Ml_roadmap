"""Local optional-library plumbing; no objective, optimizer or learner solution."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import url2pathname

from ..artifacts import file_sha256
from ..tracking_intro.demo import _mlflow, local_store, require_local_artifact_uri
from .protocol import digest


def libraries() -> tuple[Any, Any]:
    """Import only on an explicit run; no install, server, or network fallback."""
    try:
        optuna = importlib.import_module("optuna")
        mlflow = _mlflow()
    except (ModuleNotFoundError, RuntimeError) as exc:
        raise RuntimeError(
            "NOT_RUN: install declared experiments group: uv sync --group experiments"
        ) from exc
    return mlflow, optuna


def local_paths(root: Path) -> tuple[Path, Path, str, str]:
    database, artifact_root = root.resolve() / "runs.sqlite", root.resolve() / "mlflow-artifacts"
    uri, artifacts = local_store(database, artifact_root)
    return database, artifact_root, uri, artifacts


def local_model_directory(client: Any, model_id: str, artifact_root: Path) -> Path:
    logged = client.get_logged_model(model_id)
    require_local_artifact_uri(logged.artifact_location, artifact_root)
    return Path(url2pathname(urlsplit(logged.artifact_location).path)).resolve()


def model_digest(model_dir: Path) -> str:
    """Pin the entire trusted local flavor, including pickle and metadata bytes."""
    files = sorted(path for path in model_dir.rglob("*") if path.is_file())
    if not files or sum(path.stat().st_size for path in files) > 10_000_000:
        raise ValueError("model flavor missing or exceeds 10 MB")
    if any(
        path.is_symlink() or not path.resolve().is_relative_to(model_dir.resolve())
        for path in files
    ):
        raise ValueError("model flavor must contain local regular files")
    return digest({path.relative_to(model_dir).as_posix(): file_sha256(path) for path in files})
