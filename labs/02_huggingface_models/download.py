"""Явная загрузка семи разрешённых файлов; обычный import/pytest сеть не использует."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

from .protocol import read_object, verify_file


def resource_manifest() -> dict[str, Any]:
    return read_object(Path(__file__).with_name("resources.json"))


def fetch_verified(
    base_url: str,
    spec: Mapping[str, Any],
    directory: Path,
    fetch: Callable[[str, Path], None],
) -> Path:
    """Reuse exact cached bytes; refuse corrupted files instead of replacing user data."""
    name = spec["filename"]
    if not isinstance(name, str) or Path(name).name != name or any(x in name for x in "/\\:"):
        raise ValueError("filename must be one allowlisted basename")
    if name in ("", ".", ".."):
        raise ValueError("filename must be a real basename")
    destination = directory / name
    if destination.exists():
        verify_file(destination, spec["sha256"], spec["size_bytes"])
        return destination
    directory.mkdir(parents=True, exist_ok=True)
    partial = directory / (name + ".partial")
    if partial.exists():
        raise ValueError(f"unfinished download exists; inspect/remove explicitly: {partial}")
    fetch(base_url + "/" + quote(name), partial)
    verify_file(partial, spec["sha256"], spec["size_bytes"])
    partial.replace(destination)
    return destination


def download(cache_directory: Path) -> None:
    manifest = resource_manifest()
    for kind in ("model", "dataset"):
        resource = manifest[kind]
        prefix = "datasets/" if kind == "dataset" else ""
        base = f"https://huggingface.co/{prefix}{resource['id']}/resolve/{resource['revision']}"
        for spec in resource["files"]:
            maximum_bytes = int(spec["size_bytes"])

            def fetch(url: str, target: Path, maximum: int = maximum_bytes) -> None:
                total = 0
                with urlopen(url, timeout=60) as response, target.open("xb") as output:
                    while chunk := response.read(1024 * 1024):
                        total += len(chunk)
                        if total > maximum:
                            raise ValueError("download exceeds pinned file size")
                        output.write(chunk)

            path = fetch_verified(base, spec, cache_directory / resource["directory"], fetch)
            print(f"Verified {path.name}: {maximum_bytes} bytes")


def verify_cache(cache_directory: Path) -> dict[str, Any]:
    manifest = resource_manifest()
    for kind in ("model", "dataset"):
        resource = manifest[kind]
        for spec in resource["files"]:
            verify_file(
                cache_directory / resource["directory"] / spec["filename"],
                spec["sha256"],
                spec["size_bytes"],
            )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Explicit public model/data download (~111 MB)")
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/roadmap-huggingface"))
    arguments = parser.parse_args()
    download(arguments.cache_dir)


if __name__ == "__main__":
    main()
