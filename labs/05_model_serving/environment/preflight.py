"""Read-only fail-closed serving inventory check. Never installs or starts vLLM."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
from collections.abc import Mapping, Sequence
from pathlib import Path


def verify_files(root: Path, inventory: Sequence[Mapping[str, object]]) -> None:
    if not root.is_absolute() or not root.is_dir() or not inventory:
        raise ValueError("absolute existing root and nonempty inventory required")
    root = root.resolve()
    seen: set[Path] = set()
    for entry in inventory:
        name, size, checksum = entry.get("path"), entry.get("bytes"), entry.get("sha256")
        if not isinstance(name, str) or not name or Path(name).is_absolute():
            raise ValueError("invalid inventory path")
        target = (root / name).resolve()
        if not target.is_relative_to(root) or target in seen or not target.is_file():
            raise ValueError("missing, duplicate or escaping inventory path")
        seen.add(target)
        if type(size) is not int or size <= 0 or target.stat().st_size != size:
            raise ValueError("asset size mismatch")
        if not isinstance(checksum, str) or re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
            raise ValueError("missing exact SHA-256 hash")
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            for block in iter(lambda: stream.read(1048576), b""):
                digest.update(block)
        if digest.hexdigest() != checksum:
            raise ValueError("asset hash mismatch")


def check(manifest_path: Path, *, system: str | None = None) -> list[str]:
    """Return unmet gates; passing inventory is still not GPU/API validation."""
    if (system or platform.system()) != "Linux":
        return ["NOT_RUN: Linux required; Windows environments are not modified"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest object required")
        if re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("model_revision"))) is None:
            raise ValueError("exact model commit revision required")
        if manifest.get("license_reviewed") is not True:
            raise ValueError("license review required")
        if not manifest.get("server_model_id"):
            raise ValueError("server model id required")
        for root_key, files_key in (
            ("model_root", "model_files"),
            ("kernel_root", "kernel_files"),
            ("runtime_root", "runtime_files"),
        ):
            root, entries = manifest.get(root_key), manifest.get(files_key)
            if not isinstance(root, str) or not isinstance(entries, list):
                raise ValueError("asset roots and inventories must be prepared explicitly")
            if not all(isinstance(entry, dict) for entry in entries):
                raise ValueError("invalid inventory entry")
            verify_files(Path(root), entries)
        names = {entry["path"] for entry in manifest["model_files"]}
        if not {"config.json", "tokenizer_config.json", "tokenizer.json"}.issubset(names):
            raise ValueError("model config and tokenizer inventory incomplete")
        if not any(name.endswith(".safetensors") for name in names):
            raise ValueError("safetensors weights required")
        versions = manifest.get("runtime_versions")
        if not isinstance(versions, dict) or not {"vllm", "torch"}.issubset(versions):
            raise ValueError("resolved Linux runtime versions required")
        for name, version in versions.items():
            if not isinstance(name, str) or not isinstance(version, str):
                raise ValueError("runtime distribution/version strings required")
            if importlib.metadata.version(name) != version:
                raise ValueError("installed runtime version differs from manifest")
    except (OSError, ValueError, TypeError, KeyError, importlib.metadata.PackageNotFoundError):
        return ["NOT_RUN: missing or inconsistent manifest/runtime/assets; review local inventory"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors = check(args.manifest)
    for message in errors:
        print(message)
    if not errors:
        print("INVENTORY_OK: GPU tensor, CLI parser, offline launch and API remain NOT_RUN")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
