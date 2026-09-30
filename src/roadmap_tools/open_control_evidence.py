"""Read-only evidence primitives for open controls; no source execution."""

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from roadmap_tools.experiment_evidence import checked_artifact, validate_identity


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> Any:
    def invalid_constant(value: str) -> None:
        raise ValueError(f"nonfinite JSON constant: {value}")

    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=invalid_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {path.name}") from exc


def object_value(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "expected JSON object")
    return dict(value)


def ids(value: Any) -> list[str]:
    require(isinstance(value, list) and bool(value), "expected nonempty ID list")
    require(all(isinstance(x, str) and x.strip() for x in value), "invalid ID")
    require(len(value) == len(set(value)), "duplicate IDs")
    return list(value)


def same_numbers(actual: dict[str, Any], saved: Any) -> None:
    saved = object_value(saved)
    require(actual.keys() == saved.keys(), "accounting fields differ")
    for key, expected in actual.items():
        value = saved[key]
        require(type(value) in (int, float) and math.isfinite(value), "invalid numeric value")
        if type(expected) is int:
            require(type(value) is int and value == expected, "integer count differs")
        else:
            require(math.isclose(value, expected, rel_tol=1e-10, abs_tol=1e-12), "value differs")


def load_bundle(root: Path, exercise_id: str, inputs: dict[str, bytes]) -> dict[str, Any]:
    """Bind canonical inputs; first input is the primary dataset identity.

    Additional input files are independently byte-bound. Never execute artifacts.
    """
    manifest = object_value(read_json(root / "manifest.json"))
    artifacts = object_value(manifest.get("artifacts"))
    required = {*inputs, "split.json", "outputs.json", "report.md", "implementation.txt"}
    require(required <= artifacts.keys(), "missing artifact declarations")
    for name, digest in artifacts.items():
        path = checked_artifact(root, name, digest)
        require(bool(path.read_bytes().strip()), "empty artifact")
        if name in inputs:
            require(path.read_bytes() == inputs[name], "input differs from current exercise")
    validate_identity(
        manifest,
        exercise_id=exercise_id,
        dataset_sha256=hashlib.sha256(next(iter(inputs.values()))).hexdigest(),
        split_sha256=artifacts["split.json"],
    )
    require(isinstance(manifest.get("run_id"), str) and manifest["run_id"].strip(), "run ID")
    require(manifest.get("review_status") == "REQUIRES_REVIEW", "review must remain pending")
    return manifest
