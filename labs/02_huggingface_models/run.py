"""Явный запуск работы ученика: offline или реальные уже скачанные ресурсы."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import platform
import subprocess
from csv import DictReader
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .download import verify_cache
from .protocol import (
    PREPROCESSING,
    artifact_path,
    checkpoint_predictions,
    validate_comparison,
    validate_offline_artifacts,
)
from .starter import RunConfig, compare_models, prepare_splits, run_offline_experiment


def write_json(path: Path, value: object) -> str:
    payload = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def run_real(cache_directory: Path, output: Path, config: RunConfig) -> dict[str, Any]:
    """Local CSV parsing uses Datasets; remote code and downloads are never enabled here."""
    manifest = verify_cache(cache_directory)
    import sklearn
    import torch
    import transformers

    # The repository also has a top-level datasets/ reference-data directory.
    datasets = importlib.import_module("datasets")

    dataset_path = cache_directory / "dataset" / manifest["dataset"]["files"][0]["filename"]
    # This pinned CSV is ~19 MB; in-memory loading avoids Windows cache-lock path limits.
    with dataset_path.open(encoding="utf-8", newline="") as source:
        dataset = datasets.Dataset.from_list(list(DictReader(source)))
    rows = [{name: str(value) for name, value in row.items()} for row in dataset]
    splits = prepare_splits(rows, seed=config.seed)
    if output.exists() and any(output.iterdir()):
        raise ValueError("use an empty output directory to preserve previous experiments")
    output.mkdir(parents=True, exist_ok=True)
    split_ids = {
        name: [document.row_id for document in records] for name, records in splits.items()
    }
    selected = {
        "records": [asdict(document) for records in splits.values() for document in records]
    }
    data_hash = write_json(output / "selected-data.json", selected)
    split_hash = write_json(output / "splits.json", split_ids)
    results = compare_models(cache_directory / "model", splits, config, output / "checkpoint")
    labels = [document.label for document in splits["test"]]
    validate_comparison(results, labels)
    for name in ("model.safetensors", "config.json", "tokenizer.json"):
        artifact_path(output, "checkpoint/" + name)
    actual = checkpoint_predictions(
        output / "checkpoint",
        [document.text for document in splits["test"]],
        batch_size=config.batch_size,
        max_length=config.max_length,
    )
    if actual != results["adapted_encoder"]["predictions"]:
        raise ValueError("adapted report differs from checkpoint predictions")
    checkpoint_files = {
        path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (output / "checkpoint").iterdir()
        if path.is_file()
    }
    repository_root = Path(__file__).resolve().parents[2]
    code_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    code_dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "evidence": "PRETRAINED_MODEL_STUDENT_RUN",
        "seed": config.seed,
        "code_revision": code_revision,
        "code_dirty": code_dirty,
        "preprocessing": PREPROCESSING,
        "checkpoint_files": checkpoint_files,
        "config": {**asdict(config), "preprocessing": PREPROCESSING},
        "model": manifest["model"],
        "dataset": manifest["dataset"],
        "data": {"path": "selected-data.json", "sha256": data_hash},
        "splits": {"path": "splits.json", "sha256": split_hash},
        "test_ids": split_ids["test"],
        "labels": labels,
        "methods": results,
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "datasets": datasets.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "analysis": "analysis.md",
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Student encoder experiments; no implicit downloads"
    )
    parser.add_argument("mode", choices=("offline", "real", "validate-offline"))
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/roadmap-huggingface"))
    parser.add_argument("--output", type=Path, default=Path("generated-reports/huggingface"))
    parser.add_argument("--seed", type=int, default=17)
    arguments = parser.parse_args()
    config = RunConfig(seed=arguments.seed)
    if arguments.mode == "offline":
        run_offline_experiment(arguments.output, config)
    elif arguments.mode == "real":
        run_real(arguments.cache_dir, arguments.output, config)
    else:
        validate_offline_artifacts(arguments.output)
        print("OFFLINE_VALIDATED; pretrained quality: NOT_RUN")


if __name__ == "__main__":
    main()
