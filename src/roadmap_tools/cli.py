"""Command-line workflows for the learning roadmap."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from importlib import util
from io import TextIOWrapper
from pathlib import Path

from roadmap_tools.catalog import Catalog, CatalogError, CatalogItem
from roadmap_tools.tracks import TrackError, load_tracks, unique_test_targets

ProcessRunner = Callable[[Sequence[str]], int]
_PROGRESS_ENTRY = re.compile(r"^- \[([ ~x])\] (.+)$")
_CORRECTIVE_COMMAND = "uv sync --locked"
_TRAINING_MODULES = ("torch", "transformers", "datasets")
_GROUP_MODULES = {
    "training": _TRAINING_MODULES,
    "migrations": ("alembic",),
    "trainer": (*_TRAINING_MODULES, "accelerate"),
    "finetuning": (*_TRAINING_MODULES, "accelerate", "peft"),
    "sft": (*_TRAINING_MODULES, "accelerate", "peft", "trl"),
    "ranking": (*_TRAINING_MODULES, "accelerate", "sentence_transformers"),
    "tracking": ("mlflow",),
    "experiments": ("mlflow", "optuna"),
    "retrieval": ("qdrant_client",),
    "quantization": ("bitsandbytes",),
}


def main(argv: Sequence[str] | None = None, repository_root: Path | None = None) -> int:
    """Run a learning workflow command and return its process exit code."""
    # Python on Windows may inherit cp1252 when output is redirected to a pipe.
    # The curriculum contains Russian titles; keep console and captured output UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    root = Path.cwd() if repository_root is None else repository_root
    arguments = sys.argv[1:] if argv is None else argv
    return _main(arguments, root, _run_process)


def _main(argv: Sequence[str], repository_root: Path, run_process: ProcessRunner) -> int:
    """Run a command with an injectable process runner for testing."""
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    root = repository_root.resolve()

    if arguments.command == "validate-env":
        return _validate_environment()

    try:
        catalog = Catalog.load(root)
    except CatalogError as exc:
        print(f"Unable to load curriculum catalog: {exc}")
        return 2

    if arguments.command == "list":
        return _list_items(catalog)
    if arguments.command == "status":
        return _show_status(root)
    if arguments.command == "inventory":
        counts = Counter(item.kind for item in catalog.items)
        print(f"total: {len(catalog.items)}")
        for kind in ("lesson", "exercise", "lab", "project"):
            print(f"{kind}: {counts[kind]}")
        return 0
    if arguments.command in {"track", "check-track"}:
        return _run_track(
            root,
            catalog,
            arguments.identifier,
            run_process,
            check=arguments.command == "check-track",
        )
    return _run_item_tests(
        catalog, arguments.identifier, run_process, strict=arguments.command == "check"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Learning roadmap workflows")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate-env", help="check the local learning environment")
    subcommands.add_parser("list", help="list available curriculum items")
    subcommands.add_parser("status", help="show checklist entries from progress.md")
    subcommands.add_parser("inventory", help="count current material from the catalog")
    track_parser = subcommands.add_parser("track", help="show an ordered learning route")
    track_parser.add_argument("identifier")
    track_check_parser = subcommands.add_parser(
        "check-track", help="strictly check a route; human review remains separate"
    )
    track_check_parser.add_argument("identifier")
    test_parser = subcommands.add_parser("test", help="run tests for a curriculum item")
    test_parser.add_argument("identifier")
    check_parser = subcommands.add_parser("check", help="strictly check a curriculum item")
    check_parser.add_argument("identifier")
    return parser


def _validate_environment() -> int:
    python_version = ".".join(str(part) for part in sys.version_info[:3])
    uv_path = shutil.which("uv")
    python_is_supported = sys.version_info >= (3, 12)

    print(f"Python: {python_version}")
    print(f"uv: {uv_path if uv_path is not None else 'not found'}")
    print(f"Interpreter: {sys.executable}")

    if python_is_supported and uv_path is not None:
        return 0

    print(f"Corrective command: {_CORRECTIVE_COMMAND}")
    return 1


def _list_items(catalog: Catalog) -> int:
    if not catalog.items:
        print("No catalog items are currently available.")
        return 0

    for item in catalog.items:
        print(f"{item.identifier} [{item.kind}] {item.title}")
    return 0


def _show_status(repository_root: Path) -> int:
    progress_path = repository_root / "progress.md"
    try:
        lines = progress_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        print("No progress entries are currently available.")
        return 0

    entries = [match.group(0)[2:] for line in lines if (match := _PROGRESS_ENTRY.match(line))]
    if not entries:
        print("No progress entries are currently available.")
        return 0

    print("\n".join(entries))
    return 0


def _run_item_tests(
    catalog: Catalog, identifier: str, run_process: ProcessRunner, *, strict: bool = False
) -> int:
    try:
        item = catalog.get(identifier)
    except CatalogError:
        suggestions = catalog.suggest(identifier)
        message = f"Unknown catalog identifier: {identifier}"
        if suggestions:
            message += f". Did you mean: {', '.join(suggestions)}?"
        print(message)
        return 2

    if strict and not _optional_environment_available((item,)):
        return 2

    command = [sys.executable, "-m", "pytest"]
    if strict:
        command.extend(["-p", "roadmap_tools.strict_check"])
    command.extend(str(path) for path in item.tests)
    return run_process(command)


def _run_process(command: Sequence[str]) -> int:
    return subprocess.call(command)


def _optional_environment_available(items: Sequence[CatalogItem], *, track: bool = False) -> bool:
    """Check known top-level modules without loading optional ML frameworks."""
    groups = {group for item in items for group in item.requires_groups}
    if any(item.requires_training for item in items):
        groups.add("training")
    if track and groups:
        groups.add("migrations")
    ordered_groups = [group for group in _GROUP_MODULES if group in groups]
    modules = dict.fromkeys(module for group in ordered_groups for module in _GROUP_MODULES[group])
    missing = [module for module in modules if util.find_spec(module) is None]
    if not missing:
        return True
    command = "uv sync --locked" + "".join(f" --group {group}" for group in ordered_groups)
    print(f"Optional dependencies unavailable: {', '.join(missing)}. Run: {command}")
    return False


def _run_track(
    root: Path,
    catalog: Catalog,
    identifier: str,
    run_process: ProcessRunner,
    *,
    check: bool,
) -> int:
    try:
        tracks = load_tracks(root, catalog)
        if identifier not in tracks:
            raise TrackError(f"Unknown track {identifier!r}; choose: {', '.join(tracks)}")
        track = tracks[identifier]
    except TrackError as exc:
        print(f"Unable to load learning track: {exc}")
        return 2
    if not check:
        print(f"{track.identifier}: {track.title}")
        for number, key in enumerate(track.required, 1):
            print(f"{number}. {key} — {catalog.get(key).title}")
        print(f"HUMAN REVIEW REQUIRED: {track.review.relative_to(root)}")
        return 0
    if not _optional_environment_available(
        tuple(catalog.get(key) for key in track.required), track=True
    ):
        return 2
    targets = unique_test_targets(catalog, track)
    result = run_process(
        [sys.executable, "-m", "pytest", "-p", "roadmap_tools.strict_check", *map(str, targets)]
    )
    if result == 0:
        print(f"TECHNICAL CHECKS PASSED: {identifier}")
        print(f"HUMAN REVIEW REQUIRED: {track.review.relative_to(root)}")
    return result
