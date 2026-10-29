"""Wine Quality source adapter and independent submission gate (no downloads)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

from .evidence import nonempty, read_json, sha256, validate_bundle

FEATURES = (
    "fixed acidity",
    "volatile acidity",
    "citric acid",
    "residual sugar",
    "chlorides",
    "free sulfur dioxide",
    "total sulfur dioxide",
    "density",
    "pH",
    "sulphates",
    "alcohol",
)
SOURCE_URL = "https://archive.ics.uci.edu/static/public/186/wine+quality.zip"
CSV_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv"
)
LABEL_RULE = "quality>=6"
# Retrieved from the official CSV on 2026-10-28 UTC; no dataset is committed.
RAW_SIZE_BYTES = 84199
RAW_SHA256 = "4a402cf041b025d4566d954c3b9ba8635a3a8a01e039005d97d6a710278cf05e"


def prepare_records(raw: bytes) -> dict[str, Any]:
    """Deterministic parsing only: split/model choices belong to the learner."""
    digest = hashlib.sha256(raw).hexdigest()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";")
    if reader.fieldnames != [*FEATURES, "quality"]:
        raise ValueError("raw CSV schema differs from Wine Quality")
    records = []
    for index, row in enumerate(reader):
        try:
            features = {name: float(row[name]) for name in FEATURES}
            quality = int(row["quality"])
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError("raw CSV contains invalid numeric features/target") from error
        if not all(math.isfinite(value) for value in features.values()) or quality not in range(11):
            raise ValueError("raw CSV contains nonfinite features or invalid quality")
        group = hashlib.sha256(json.dumps(features, sort_keys=True).encode()).hexdigest()
        records.append(
            {
                "row_id": f"wine:{digest[:16]}:{index}",
                "source_row": index,
                "features": features,
                "label": int(quality >= 6),
                "group_id": group,
            }
        )
    if not records:
        raise ValueError("raw CSV must contain rows")
    return {
        "classes": [0, 1],
        "features": list(FEATURES),
        "label_rule": LABEL_RULE,
        "records": records,
    }


def validate_source_rows(root: Path) -> dict[str, Any]:
    """Hash verification is done by bundle gate; this also verifies the derivation."""
    from .evidence import artifact_path, check_equal

    manifest = read_json(root / "manifest.json")
    refs = manifest.get("artifacts", {})
    if not isinstance(refs, dict) or not {"raw", "data"}.issubset(refs):
        raise ValueError("raw source/data references are required")
    raw_path = artifact_path(root, refs["raw"].get("path", ""))
    data = read_json(artifact_path(root, refs["data"].get("path", "")))
    check_equal(data, prepare_records(raw_path.read_bytes()), "source raw features/labels/IDs")
    return data


def replay_tabular(
    data: dict[str, Any],
    splits: dict[str, Any],
    methods: dict[str, Any],
    study: dict[str, Any],
    *,
    evaluation_split: str = "test",
) -> None:
    """Refit a bounded declarative model family; never deserialize executable models."""
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeClassifier

    from .evidence import check_equal, finite

    configs = study.get("configs", {})
    linear, tree = configs.get("linear", {}), configs.get("tree", {})
    if set(linear) != {"C"} or not finite(linear["C"]) or linear["C"] <= 0:
        raise ValueError("linear config requires positive finite C only")
    allowed = {"kind", "max_depth", "min_samples_leaf"}
    if tree.get("kind") == "random_forest":
        allowed.add("n_estimators")
    elif tree.get("kind") != "decision_tree":
        raise ValueError("tree kind must be decision_tree or random_forest")
    if set(tree) != allowed:
        raise ValueError("tree config fields differ from replay contract")
    for key in allowed - {"kind"}:
        if type(tree[key]) is not int or tree[key] < 1:
            raise ValueError("tree config values must be positive integers")
    seed = study.get("seed")
    if type(seed) is not int or seed < 0:
        raise ValueError("model seed must be nonnegative integer")
    rows = {row["row_id"]: row for row in data["records"]}
    train = [[rows[row_id]["features"][name] for name in FEATURES] for row_id in splits["train"]]
    labels = [rows[row_id]["label"] for row_id in splits["train"]]
    evaluation = [
        [rows[row_id]["features"][name] for name in FEATURES] for row_id in splits[evaluation_split]
    ]
    params = {key: value for key, value in tree.items() if key != "kind"}
    if tree["kind"] == "decision_tree":
        stronger: Any = DecisionTreeClassifier(**params, random_state=seed)
    else:
        stronger = RandomForestClassifier(**params, random_state=seed, n_jobs=1)
    estimators = {
        "dummy": DummyClassifier(strategy="most_frequent"),
        "linear": make_pipeline(
            StandardScaler(), LogisticRegression(C=linear["C"], random_state=seed)
        ),
        "tree": stronger,
    }
    for name, method in methods.items():
        estimator = estimators[name].fit(train, labels)
        check_equal(
            method.get("predictions"),
            [int(x) for x in estimator.predict(evaluation)],
            f"replayed {name} predictions",
        )


def validate_submission(root: Path) -> dict[str, Any]:
    data = validate_source_rows(root)
    result = validate_bundle(root, project_id="ml-external-tabular")
    source = result["source"]
    if source["provider"] != "UCI Wine Quality" or source["url"] not in {SOURCE_URL, CSV_URL}:
        raise ValueError("external source must be the documented UCI Wine Quality route")
    if source["license"] != "CC-BY-4.0":
        raise ValueError("record UCI CC-BY-4.0 attribution/license")
    raw = result["files"]["raw"]
    if raw.stat().st_size != RAW_SIZE_BYTES or sha256(raw) != RAW_SHA256:
        raise ValueError("pinned raw UCI red-wine bytes differ; do not relabel a fixture")
    if len(data["records"]) != 1599:
        raise ValueError("external Wine Quality study requires the full red-wine source")
    analysis = read_json(result["files"]["study"])
    for field in (
        "feature_availability",
        "leakage_audit",
        "split_rationale",
        "selection_rule",
        "error_analysis",
        "limitations",
        "transfer_question",
    ):
        nonempty(analysis.get(field), field)
    selection = analysis.get("selection", {})
    if selection.get("used_split") != "validation" or selection.get("selected_method") not in {
        "linear",
        "tree",
    }:
        raise ValueError("selection must use validation and choose linear/tree before test")
    revision = analysis.get("code_revision")
    if (
        not isinstance(revision, str)
        or len(revision) != 40
        or any(char not in "0123456789abcdef" for char in revision)
    ):
        raise ValueError("code_revision must record full Git SHA")
    for key in ("python", "numpy", "sklearn"):
        nonempty(analysis.get("versions", {}).get(key), f"version {key}")
    if type(analysis.get("seed")) is not int or analysis["seed"] < 0:
        raise ValueError("seed must be nonnegative integer")
    replay_tabular(data, result["splits"], result["evaluation"]["methods"], analysis)
    # Repeated complete training is a different requirement from conditional bootstrap.
    repeated = analysis.get("repeated_runs")
    if not isinstance(repeated, list) or len(repeated) < 3:
        raise ValueError("at least three full-training run artifact references are required")
    seen: set[int] = set()
    for run in repeated:
        if not isinstance(run, dict) or type(run.get("seed")) is not int or run["seed"] in seen:
            raise ValueError("repeated training requires distinct integer seeds")
        seen.add(run["seed"])
        logical = run.get("artifact")
        if logical not in result["files"] or not str(logical).startswith("repeat_"):
            raise ValueError("repeated training must reference saved hashed run artifacts")
        saved = read_json(result["files"][logical])
        if saved.get("seed") != run["seed"]:
            raise ValueError("repeated seed differs from saved artifact")
        ids = saved.get("row_ids")
        if ids != result["splits"]["validation"]:
            raise ValueError("repeated training comparisons must use locked validation IDs")
        from .evidence import check_equal, classification_metrics

        by_id = {row["row_id"]: row for row in data["records"]}
        labels = [by_id[row_id]["label"] for row_id in ids]
        check_equal(saved.get("labels"), labels, "repeat labels")
        if set(saved.get("methods", {})) != {"linear", "tree"}:
            raise ValueError("repeat must retrain both candidate families")
        for method in saved["methods"].values():
            check_equal(
                method.get("metrics"),
                classification_metrics(labels, method.get("predictions", []), data["classes"]),
                "repeated-run metrics",
            )
        nonempty(saved.get("training_log"), "training log")
        replay_tabular(
            data,
            result["splits"],
            saved["methods"],
            {**analysis, "seed": run["seed"]},
            evaluation_split="validation",
        )
    return {
        "technical_status": "VERIFIED",
        "project_id": "ml-external-tabular",
        "human_review": "REQUIRED",
        "authorship": "NOT_AUTOMATICALLY_VERIFIED",
        "raw_sha256": sha256(result["files"]["raw"]),
        "methods": sorted(result["evaluation"]["methods"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline verification of an external wine study")
    parser.add_argument("submission", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_submission(args.submission), indent=2))


if __name__ == "__main__":
    main()
