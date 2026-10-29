"""Offline evidence consistency checks; engine provenance still needs human review."""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PureWindowsPath
from typing import cast

_MAX_BYTES = 1_048_576
_ROLES = frozenset({"initial", "restarted", "environment", "lock", "server_log", "defense"})


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be an object")
    return cast(dict[str, object], value)


def _number(value: object, name: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be a finite number")
    result = float(cast(float, value))
    if not math.isfinite(result) or result < 0 or (positive and result == 0):
        raise ValueError(f"{name} must be finite and nonnegative (positive if required)")
    return result


def validate_records(records: Sequence[Mapping[str, object]], elapsed_s: float) -> None:
    """Validate timing units and observation identities without computing learner statistics."""
    elapsed = _number(elapsed_s, "elapsed_s", positive=True)
    if not records or len(records) > 256:
        raise ValueError("records must contain 1..256 bounded observations")
    identities: set[int] = set()
    for record in records:
        identity = record.get("request_index")
        if type(identity) is not int or identity < 0 or identity in identities:
            raise ValueError("request_index must be a distinct nonnegative integer")
        identities.add(identity)
        if record.get("status") not in {"ok", "error", "deadline"}:
            raise ValueError("unknown request status")
        e2e = _number(record.get("e2e_ms"), "e2e_ms", positive=record.get("status") == "ok")
        queue = _number(record.get("queue_ms"), "queue_ms")
        if e2e + queue > elapsed * 1000 + 1:
            raise ValueError("request duration exceeds batch wall time")
        if record.get("ttft_ms") is not None:
            first = _number(record["ttft_ms"], "ttft_ms")
            if first > e2e:
                raise ValueError("ttft_ms cannot exceed e2e_ms")
        tokens = record.get("completion_tokens")
        if tokens is not None and (type(tokens) is not int or tokens < 0):
            raise ValueError("completion_tokens must be a nonnegative integer or null")


def validate_run(document: object) -> dict[str, object]:
    """Validate one saved endpoint report, never contact its endpoint."""
    report = _mapping(document, "endpoint report")
    if type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        raise ValueError("unsupported endpoint schema")
    if report.get("evidence") != "live_endpoint":
        raise ValueError("live_endpoint required; synthetic fixture is not live evidence")
    if report.get("state") not in {"cold", "warm"}:
        raise ValueError("state must be cold or warm")
    if type(report.get("concurrency")) is not int or report["concurrency"] not in (1, 2):
        raise ValueError("concurrency must be 1 or 2")
    config = _mapping(report.get("request_config"), "request_config")
    limit = config.get("max_tokens")
    if type(limit) is not int or not 1 <= limit <= 128:
        raise ValueError("bounded max_tokens required")
    if type(config.get("attempts_per_request")) is not int or config["attempts_per_request"] != 1:
        raise ValueError("no automatic replay permitted")
    if _number(config.get("deadline_s"), "deadline_s", positive=True) > 120:
        raise ValueError("deadline exceeds existing client budget")
    raw = report.get("raw")
    if not isinstance(raw, list) or not 1 <= len(raw) <= 8:
        raise ValueError("expected existing endpoint raw records (1..8)")
    rows = [_mapping(row, "raw record") for row in raw]
    elapsed = _number(report.get("run_elapsed_s"), "run_elapsed_s", positive=True)
    validate_records(rows, elapsed)
    summarize = importlib.import_module("labs.05_model_serving.experiments.report").summarize
    if report.get("summary") != summarize(rows, elapsed_s=elapsed, evidence="live_endpoint"):
        raise ValueError("saved summary disagrees with raw measurements")
    return report


def _read_file(root: Path, relative: object) -> tuple[Path, bytes]:
    if not isinstance(relative, str) or not relative or PureWindowsPath(relative).anchor:
        raise ValueError("artifact path must be relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("artifact path is absent or escapes evidence directory")
    with path.open("rb") as source:
        content = source.read(_MAX_BYTES + 1)
    if not content or len(content) > _MAX_BYTES:
        raise ValueError("artifact size must be 1..1048576 bytes")
    return path, content


def load_evidence(directory: Path) -> dict[str, object]:
    """Read bounded evidence files and cross-check identity after restart."""
    root = directory.resolve()
    _, content = _read_file(root, "evidence.json")
    manifest = _mapping(json.loads(content), "manifest")
    if (
        type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
        or manifest.get("status") != "RECORDED_REQUIRES_REVIEW"
        or manifest.get("provider") != "vllm"
    ):
        raise ValueError("recorded vLLM evidence required; NOT_RUN cannot pass")
    revision = manifest.get("model_revision")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("exact model_revision required")
    for field in ("model_repo", "server_model_id"):
        if not isinstance(manifest.get(field), str) or not str(manifest[field]).strip():
            raise ValueError(f"{field} required")
    command = manifest.get("server_command")
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(part, str) or not part.strip() for part in command)
    ):
        raise ValueError("server_command must contain the actual invocation arguments")
    artifacts = _mapping(manifest.get("artifacts"), "artifacts")
    if artifacts.keys() != _ROLES:
        raise ValueError("initial/restarted/environment/lock/server_log/defense artifacts required")
    payloads: dict[str, bytes] = {}
    paths: set[Path] = set()
    for role, value in artifacts.items():
        entry = _mapping(value, role)
        path, content = _read_file(root, entry.get("path"))
        if path in paths:
            raise ValueError("artifact roles require distinct files")
        paths.add(path)
        if hashlib.sha256(content).hexdigest() != entry.get("sha256"):
            raise ValueError(f"artifact hash mismatch: {role}")
        payloads[role] = content
    for role in ("lock", "server_log", "defense"):
        try:
            if not payloads[role].decode("utf-8").strip():
                raise ValueError(f"{role} must contain readable evidence")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{role} must be UTF-8 text") from exc
    environment = _mapping(json.loads(payloads["environment"]), "environment")
    if environment.get("system") != "Linux":
        raise ValueError("real Linux/WSL runtime evidence required")
    for field in ("gpu", "driver", "vllm"):
        if not isinstance(environment.get(field), str) or not str(environment[field]).strip():
            raise ValueError(f"environment {field} required")
    initial = validate_run(json.loads(payloads["initial"]))
    restarted = validate_run(json.loads(payloads["restarted"]))
    for run in (initial, restarted):
        runtime = _mapping(run.get("runtime_and_model"), "runtime_and_model")
        versions = _mapping(runtime.get("runtime_versions"), "runtime_versions")
        if (
            runtime.get("model_revision") != revision
            or runtime.get("server_model_id") != manifest["server_model_id"]
            or run.get("model_server_id") != manifest["server_model_id"]
            or versions.get("vllm") != environment["vllm"]
        ):
            raise ValueError("model/runtime identity changed across restart")
        if _mapping(run["summary"], "summary")["completed"] == 0:
            raise ValueError("at least one completed request per run required")
    if initial["state"] != "warm" or len(cast(list[object], initial["raw"])) < 2:
        raise ValueError("initial warm measurement needs at least two observations")
    return {
        "manifest": manifest,
        "initial": initial,
        "restarted": restarted,
        "review": "REQUIRES_REVIEW",
    }
