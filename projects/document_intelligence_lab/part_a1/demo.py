"""Tiny authored shape inventory: rules versus train-only fitted TF-IDF pipeline.

Explicit --output NEW_DIRECTORY; no network, pretrained model or student imports.
"""

from __future__ import annotations

import argparse
import hashlib
import pickle
import platform
import subprocess
import time
import uuid
from importlib.metadata import version
from pathlib import Path
from typing import Any

from ..artifacts import (
    PREPROCESSING,
    file_sha256,
    json_bytes,
    load_trusted_local_classifier,
    read_json,
    write_run_new,
)
from ..contracts import (
    classification_metrics,
    normalize_document,
    validate_dataset,
    validate_splits,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _code_identity() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = "unknown-no-git-metadata", True
    package = Path(__file__).parent.parent
    source = b"".join(
        path.relative_to(package).as_posix().encode() + b"\0" + path.read_bytes() + b"\0"
        for path in (package / "contracts.py", package / "artifacts.py", Path(__file__))
    )
    return {
        "revision": revision,
        "dirty": dirty,
        "source_sha256": hashlib.sha256(source).hexdigest(),
    }


def run_demo(output: Path, *, seed: int = 17) -> Path:
    """Compare two teacher methods on one frozen cohort; return a NEW run directory."""
    if output.exists():
        raise FileExistsError(f"demo output already exists: {output}")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    import numpy
    import sklearn
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    data_path, split_path, sources_path = (
        FIXTURES / name for name in ("data.json", "splits.json", "sources.json")
    )
    dataset = validate_dataset(read_json(data_path))
    splits = validate_splits(read_json(split_path), dataset)
    rows = dataset.by_id
    rule_model: dict[str, Any] = {
        "schema_version": 1,
        "labels": list(dataset.labels),
        "rules": [{"token": "circle", "label": "circle"}, {"token": "square", "label": "square"}],
        "fallback_label": "circle",
    }
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 1), lowercase=False)),
            ("classifier", LogisticRegression(C=1.0, random_state=seed, max_iter=300)),
        ]
    )
    started = time.perf_counter()
    pipeline.fit(
        [normalize_document(rows[row].text) for row in splits["train"]],
        [rows[row].label for row in splits["train"]],
    )
    fit_seconds = time.perf_counter() - started

    def predict(method: str, ids: tuple[str, ...]) -> list[dict[str, str]]:
        texts = [normalize_document(rows[row].text) for row in ids]
        if method == "rules":
            labels = [
                next(
                    (
                        rule["label"]
                        for rule in rule_model["rules"]
                        if rule["token"] in text.split()
                    ),
                    rule_model["fallback_label"],
                )
                for text in texts
            ]
        else:
            labels = [str(label) for label in pipeline.predict(texts)]
        return [
            {"row_id": row_id, "predicted_label": label}
            for row_id, label in zip(ids, labels, strict=True)
        ]

    methods = ("rules", "tfidf-linear")
    validation = {
        method: classification_metrics(
            dataset, splits["validation"], predict(method, splits["validation"])
        )
        for method in methods
    }
    # Select once on validation; only after this line may test predictions be read.
    selected = min(methods, key=lambda method: (-validation[method]["macro_f1"], method))
    selection: dict[str, Any] = {
        "criterion": "validation macro_f1 descending; method name ascending on ties",
        "selected_method": selected,
        "frozen_before_test": True,
        "validation_metrics": validation,
        "candidate_config": {
            "rules": "two literal shape rules, fallback circle",
            "tfidf-linear": {"C": 1.0, "max_iter": 300, "ngram_range": [1, 1]},
        },
    }
    code = _code_identity()
    versions = {
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "scipy": version("scipy"),
        "sklearn": sklearn.__version__,
    }
    output.mkdir(parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex
    inventory = {}
    for method in methods:
        started = time.perf_counter()
        predictions = predict(method, splits["test"])
        elapsed = time.perf_counter() - started
        timing = {
            "name": "test_inference",
            "value": elapsed,
            "unit": "seconds",
            "device": "cpu",
            "sample_count": len(predictions),
            "batch_size": len(predictions),
            "condition": "warm",
        }
        timings = [timing]
        if method == "tfidf-linear":
            timings.append(
                {
                    **timing,
                    "name": "fit",
                    "value": fit_seconds,
                    "sample_count": len(splits["train"]),
                    "batch_size": len(splits["train"]),
                    "condition": "cold",
                }
            )
        manifest = {
            "schema_version": 1,
            "exercise_id": "document-a1-teacher",
            "dataset_sha256": file_sha256(data_path),
            "split_sha256": file_sha256(split_path),
            "config": {
                "seed": seed,
                "selection": selection,
                "method_config": selection["candidate_config"][method],
            },
            "method": method,
            "evidence_kind": "AUTHOR_SYNTHETIC_SMOKE_ONLY",
            "run_id": f"{run_id}-{method}",
            "code": code,
            "versions": versions,
            "labels": list(dataset.labels),
            "preprocessing": PREPROCESSING,
            "model": {
                "id": f"a1-{method}",
                "revision": "1",
                "format": "rules-json-v1" if method == "rules" else "sklearn-pickle-v1",
            },
        }
        manifest_path = write_run_new(
            output / method,
            data=data_path,
            splits=split_path,
            sources=sources_path,
            model=json_bytes(rule_model)
            if method == "rules"
            else pickle.dumps(pipeline, protocol=5),
            predictions=predictions,
            manifest=manifest,
            measurement={
                "timings": timings,
                "memory_bytes": None,
                "memory_unknown_reason": (
                    "CPU process/native peak memory was not instrumented; "
                    "timing is not a memory estimate."
                ),
            },
            selection={
                **selection,
                "selected_method": method,
                "comparison_selected_method": selected,
            },
        )
        digest = file_sha256(manifest_path)
        load_trusted_local_classifier(output / method, digest, trusted_local_artifact=True)
        inventory[method] = {
            "manifest_sha256": digest,
            "test_metrics": classification_metrics(dataset, splits["test"], predictions),
        }
    (output / "comparison.json").write_bytes(
        json_bytes(
            {
                "evidence_kind": "AUTHOR_SYNTHETIC_SMOKE_ONLY",
                "pretrained_quality": "NOT_RUN",
                "dataset_sha256": file_sha256(data_path),
                "split_sha256": file_sha256(split_path),
                "selection": selection,
                "methods": inventory,
            }
        )
    )
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    print(run_demo(args.output, seed=args.seed))
