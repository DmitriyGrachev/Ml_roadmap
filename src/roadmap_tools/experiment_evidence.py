"""Small, read-only checks for locally saved experiment evidence.

Exercise packages own the meaning of their data, predictions, and metrics.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Mapping
from pathlib import Path, PureWindowsPath

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def checked_artifact(root: Path, relative_path: str, sha256: str) -> Path:
    """Return a saved file within root only when its actual bytes match sha256."""
    if (
        not isinstance(relative_path, str)
        or not relative_path
        or "\\" in relative_path
        or ":" in relative_path
        or "\x00" in relative_path
        or relative_path.startswith("/")
        or PureWindowsPath(relative_path).drive
        or any(part in {"", ".", ".."} for part in relative_path.split("/"))
    ):
        raise ValueError("artifact path must be a portable relative file path")
    if not _valid_sha256(sha256):
        raise ValueError("artifact sha256 must be lowercase SHA-256")
    resolved_root = root.resolve()
    resolved = (resolved_root / relative_path).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError("artifact path escapes its root")
    if not resolved.is_file():
        raise ValueError("artifact file is missing")
    try:
        with resolved.open("rb") as source:
            actual = hashlib.file_digest(source, "sha256").hexdigest()
    except OSError as exc:
        raise ValueError("artifact file is unreadable") from exc
    if actual != sha256:
        raise ValueError("artifact sha256 differs from saved bytes")
    return resolved


def _finite_config(value: object) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_finite_config(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _finite_config(item) for key, item in value.items())
    return False


def validate_identity(
    manifest: Mapping[str, object],
    *,
    exercise_id: str,
    dataset_sha256: str,
    split_sha256: str,
) -> None:
    """Check schema-1 identity and JSON-shaped finite configuration values.

    This does not authenticate reported predictions or assess model quality.
    Each exercise must compare its saved records and actual inference separately.
    """
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError("unsupported schema_version")
    if not isinstance(exercise_id, str) or not exercise_id.strip():
        raise ValueError("expected exercise_id must be nonempty text")
    if manifest.get("exercise_id") != exercise_id:
        raise ValueError("exercise_id does not match")
    for field, expected in (
        ("dataset_sha256", dataset_sha256),
        ("split_sha256", split_sha256),
    ):
        if not _valid_sha256(expected) or manifest.get(field) != expected:
            raise ValueError(f"{field} does not match a lowercase SHA-256 identity")
    config = manifest.get("config")
    if not isinstance(config, Mapping) or not _finite_config(config):
        raise ValueError("config must contain only finite JSON values")
