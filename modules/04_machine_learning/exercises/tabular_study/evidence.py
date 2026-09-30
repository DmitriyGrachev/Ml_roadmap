"""Explicitly trusted local inference replay."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline

from roadmap_tools.experiment_evidence import checked_artifact, validate_identity


def _read(path: Path) -> Any:
    def reject(value: str) -> None:
        raise ValueError(f"nonfinite JSON: {value}")

    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {path.name}") from exc


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _object(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "expected JSON object")
    return dict(value)


def _ids(value: Any) -> list[str]:
    _require(isinstance(value, list) and bool(value), "IDs must be a nonempty array")
    _require(all(isinstance(x, str) and x for x in value), "IDs must be strings")
    _require(len(value) == len(set(value)), "duplicate IDs")
    return list(value)


def _same(actual: Any, saved: Any) -> None:
    if isinstance(actual, dict):
        _require(isinstance(saved, dict) and actual.keys() == saved.keys(), "metric fields differ")
        for key in actual:
            _same(actual[key], saved[key])
    elif isinstance(actual, list):
        _require(isinstance(saved, list) and len(actual) == len(saved), "metric bins differ")
        for left, right in zip(actual, saved, strict=True):
            _same(left, right)
    elif isinstance(actual, (int, float)):
        _require(type(saved) in (int, float) and math.isfinite(saved), "nonfinite metric")
        _require(math.isclose(actual, saved, rel_tol=1e-9, abs_tol=1e-10), "metric differs")
    else:
        _require(actual == saved, "metric differs")


def _check_splits(frame: pd.DataFrame, split: dict[str, Any]) -> list[str]:
    dev, test = _ids(split.get("development_ids")), _ids(split.get("test_ids"))
    _require(not set(dev) & set(test), "development/test membership overlaps")
    _require(set(dev + test) == set(frame.index), "split membership does not cover dataset")

    def separate(left: list[str], right: list[str]) -> None:
        _require(
            not set(frame.loc[left, "group_id"]) & set(frame.loc[right, "group_id"]),
            "group membership overlaps",
        )

    separate(dev, test)
    folds: Any = split.get("folds")
    _require(isinstance(folds, list) and len(folds) == 3, "exactly three development folds")
    all_validation: list[str] = []
    for fold in folds:
        fold = _object(fold)
        train, validation = _ids(fold.get("train_ids")), _ids(fold.get("validation_ids"))
        _require(not set(train) & set(validation), "fold membership overlaps")
        _require(set(train + validation) == set(dev), "fold must partition development only")
        separate(train, validation)
        all_validation.extend(validation)
    _require(sorted(all_validation) == sorted(dev), "each development row validates once")
    return test


def _metrics(labels: Any, probabilities: Any, decisions: Any, channels: Any) -> dict[str, Any]:
    bins = []
    for lower, upper in ((0.0, 0.5), (0.5, 1.0)):
        mask = (probabilities >= lower) & ((probabilities < upper) if upper < 1 else True)
        count = int(mask.sum())
        bins.append(
            {
                "lower": lower,
                "upper": upper,
                "count": count,
                "mean_probability": float(probabilities[mask].mean()) if count else None,
                "positive_rate": float(labels[mask].mean()) if count else None,
            }
        )
    slices = {}
    for channel in sorted(set(channels)):
        mask = channels == channel
        slices[channel] = {
            "count": int(mask.sum()),
            "fp": int(((labels == 0) & (decisions == 1) & mask).sum()),
            "fn": int(((labels == 1) & (decisions == 0) & mask).sum()),
        }
    return {
        "count": len(labels),
        "accuracy": float(accuracy_score(labels, decisions)),
        "brier": float(brier_score_loss(labels, probabilities)),
        "log_loss": float(log_loss(labels, probabilities, labels=[0, 1])),
        "fp": int(((labels == 0) & (decisions == 1)).sum()),
        "fn": int(((labels == 1) & (decisions == 0)).sum()),
        "reliability": bins,
        "slices": slices,
    }


def _probabilities(rows: Any, ids: list[str]) -> Any:
    _require(
        isinstance(rows, list) and all(isinstance(r, dict) for r in rows),
        "invalid development prediction rows",
    )
    _require([r.get("row_id") for r in rows] == ids, "development prediction IDs differ")
    values = [r.get("probability") for r in rows]
    _require(
        all(type(p) in (float, int) and math.isfinite(p) and 0 <= p <= 1 for p in values),
        "invalid development probabilities",
    )
    return np.asarray(values, dtype=np.float64)


def _study(
    root: Path,
    manifest: dict[str, Any],
    frame: pd.DataFrame,
    split: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    study = _object(_read(checked_artifact(root, "study.json", manifest.get("study_sha256", ""))))
    candidates = config["candidates"]
    allowed_families = {
        "Dummy",
        "LogisticRegression",
        "TreeOrRandomForest",
        "HistGradientBoostingClassifier",
    }
    for candidate in candidates:
        family = candidate.get("family")
        calibration = candidate.get("calibration")
        feature_set = candidate.get("feature_set")
        _require(
            isinstance(family, str) and family in allowed_families,
            "candidate family is unsupported",
        )
        _require(
            isinstance(calibration, str) and calibration in {"raw", "sigmoid"},
            "candidate calibration must be raw or sigmoid",
        )
        _require(
            isinstance(feature_set, str) and bool(feature_set.strip()),
            "candidate feature_set must be nonempty text",
        )
    _ids([c.get("id") for c in candidates])
    by_id = {c["id"]: c for c in candidates}
    _require(config.get("selected_id") in by_id, "selected configuration is unknown")
    _require(
        {c["family"] for c in candidates} == allowed_families,
        "four candidate families required",
    )
    runs: Any = study.get("runs")
    _require(
        isinstance(runs, list) and len(runs) == len(candidates) * 3,
        "all candidates need the same three folds",
    )
    predictions: dict[tuple[str, int], Any] = {}
    for run in runs:
        run = _object(run)
        config_id, fold_id = run.get("config_id"), run.get("fold_id")
        _require(
            isinstance(config_id, str)
            and config_id in by_id
            and type(fold_id) is int
            and 0 <= fold_id < 3,
            "unknown run configuration/fold",
        )
        key = (str(config_id), int(run["fold_id"]))
        _require(key not in predictions, "duplicate run")
        ids = split["folds"][fold_id]["validation_ids"]
        proba = _probabilities(run.get("predictions"), ids)
        labels = frame.loc[ids, "outcome"].to_numpy(dtype=int)
        _same(float(brier_score_loss(labels, proba)), run.get("brier"))
        _same(float(log_loss(labels, proba, labels=[0, 1])), run.get("log_loss"))
        predictions[key] = proba
    calibration, ablation = _object(study.get("calibration")), _object(study.get("ablation"))
    for pair, left, right, field in (
        (calibration, "raw", "sigmoid", "calibration"),
        (ablation, "with_feature", "without_feature", "feature_set"),
    ):
        a, b = pair.get(left), pair.get(right)
        _require(
            isinstance(a, str) and isinstance(b, str) and a != b and a in by_id and b in by_id,
            "comparison needs two actual configuration IDs",
        )
        first, second = by_id[a], by_id[b]
        _require(
            {k: v for k, v in first.items() if k not in {"id", field}}
            == {k: v for k, v in second.items() if k not in {"id", field}},
            "comparison must change only calibration or feature set",
        )
        _require(first.get(field) != second.get(field), "comparison configuration must differ")
    _require(
        by_id[calibration["raw"]].get("calibration") == "raw"
        and by_id[calibration["sigmoid"]].get("calibration") == "sigmoid",
        "calibration requires raw and sigmoid results",
    )
    _require(
        all(
            isinstance(ablation.get(k), str) and ablation[k].strip()
            for k in ("feature", "availability")
        ),
        "missing feature availability rationale",
    )
    importance = _object(study.get("permutation_importance"))
    importance_key = (importance.get("config_id"), importance.get("fold_id"))
    _require(
        importance_key in predictions and isinstance(importance.get("feature"), str),
        "importance must refer to an actual validation run",
    )
    key = (str(importance["config_id"]), int(importance["fold_id"]))
    ids = split["folds"][key[1]]["validation_ids"]
    permuted = _probabilities(importance.get("predictions"), ids)
    labels = frame.loc[ids, "outcome"].to_numpy(dtype=int)
    _same(
        float(brier_score_loss(labels, permuted) - brier_score_loss(labels, predictions[key])),
        importance.get("brier_increase"),
    )
    comparison = _object(study.get("paired_comparison"))
    a, b = comparison.get("config_a"), comparison.get("config_b")
    _require(
        isinstance(a, str) and isinstance(b, str) and a in by_id and b in by_id and a != b,
        "paired comparison must reference actual runs",
    )
    checked_artifact(root, "paired/manifest.json", manifest.get("paired_sha256", ""))
    paired = root / "paired"
    importlib.import_module(
        "modules.03_data_foundations.exercises.paired_model_comparison.evidence"
    ).validate_evidence(paired)
    paired_manifest = _object(_read(paired / "manifest.json"))
    _require(paired_manifest["config"]["loss"] == "squared_error", "paired loss must be Brier")
    snapshot = _read(paired / "snapshot.json")
    dev = split["development_ids"]
    expected_snapshot = [
        {"row_id": i, "unit_id": frame.loc[i, "group_id"], "label": int(frame.loc[i, "outcome"])}
        for i in dev
    ]
    _require(snapshot == expected_snapshot, "paired snapshot differs from development data")
    _require(
        _read(paired / "split.json")["evaluation_row_ids"] == dev,
        "paired split differs from development IDs",
    )
    by_row: dict[tuple[str, str], float] = {}
    for (candidate, fold), proba in predictions.items():
        for row_id, value in zip(split["folds"][fold]["validation_ids"], proba, strict=True):
            by_row[candidate, row_id] = float(value)
    reliability = _object(calibration.get("reliability"))
    labels = frame.loc[dev, "outcome"].to_numpy(dtype=int)
    channels = frame.loc[dev, "channel"].to_numpy()
    for name in ("raw", "sigmoid"):
        proba = np.asarray([by_row[calibration[name], row_id] for row_id in dev], dtype=np.float64)
        _same(
            _metrics(labels, proba, (proba >= config["threshold"]).astype(int), channels)[
                "reliability"
            ],
            reliability.get(name),
        )
    for row in _read(paired / "predictions.json"):
        _same(by_row[str(a), row["row_id"]], row["prediction_a"])
        _same(by_row[str(b), row["row_id"]], row["prediction_b"])
    return _object(study.get("evaluation_report"))


def _binary_metrics(labels: Any, probability: Any, decision: Any) -> dict[str, Any]:
    return {
        "count": len(labels),
        "accuracy": float(accuracy_score(labels, decision)),
        "precision": float(precision_score(labels, decision, zero_division=0)),
        "recall": float(recall_score(labels, decision, zero_division=0)),
        "f1": float(f1_score(labels, decision, zero_division=0)),
        "brier": float(brier_score_loss(labels, probability)),
    }


def _check_report(
    report: dict[str, Any],
    manifest: dict[str, Any],
    labels: Any,
    probability: Any,
    decision: Any,
    channels: Any,
) -> None:
    for key, value in (
        ("threshold", manifest["config"]["threshold"]),
        ("seed", manifest["config"]["seed"]),
        ("dataset_sha256", manifest["dataset_sha256"]),
        ("schema_version", 1),
        ("model_name", manifest["config"]["selected_id"]),
    ):
        _same(value, report.get(key))
    _same(_binary_metrics(labels, probability, decision), report.get("metrics"))
    slices = {}
    for channel in sorted(set(channels)):
        mask = channels == channel
        slices[channel] = _binary_metrics(labels[mask], probability[mask], decision[mask])
    _same(slices, report.get("slices"))
    versions = _object(report.get("versions"))
    _require(
        set(versions) == {"python", "numpy", "scikit_learn"}
        and all(isinstance(v, str) and v for v in versions.values()),
        "invalid report versions",
    )


def validate_evidence(root: Path, *, trusted_model_path: Path | None = None) -> None:
    """Replay saved holdout inference; never grants trust based on a digest.

    Only pass a path to a pipeline you produced locally and explicitly trust to
    execute Python. Successful replay proves internal consistency, not provenance,
    selection chronology, scientific quality, or completion of human review.
    """
    manifest = _object(_read(root / "manifest.json"))
    validate_identity(
        manifest,
        exercise_id="ml-tabular-study",
        dataset_sha256=manifest.get("dataset_sha256", ""),
        split_sha256=manifest.get("split_sha256", ""),
    )
    paths = {
        name: checked_artifact(root, filename, manifest.get(f"{name}_sha256", ""))
        for name, filename in (
            ("dataset", "dataset.csv"),
            ("split", "split.json"),
            ("config", "config.json"),
            ("model", "model.pkl"),
            ("predictions", "predictions.json"),
        )
    }
    config = _object(_read(paths["config"]))
    _require(config == manifest["config"], "config differs from saved configuration")
    _require(type(config.get("seed")) is int and config["seed"] >= 0, "invalid seed")
    threshold: Any = config.get("threshold")
    _require(type(threshold) in (int, float) and 0 <= threshold <= 1, "invalid threshold")
    candidates: Any = config.get("candidates")
    _require(
        isinstance(candidates, list) and 1 <= len(candidates) <= 12,
        "candidate budget must be between 1 and 12, baseline included",
    )
    _require(all(isinstance(c, dict) and bool(c) for c in candidates), "invalid candidates")
    _require(type(config.get("reruns")) is int and config["reruns"] >= 0, "invalid reruns")
    elapsed: Any = config.get("elapsed_seconds")
    _require(type(elapsed) in (int, float) and elapsed >= 0, "invalid elapsed time")
    features = _ids(config.get("features"))
    _require(
        not set(features) & {"row_id", "group_id", "time_id", "outcome"},
        "identity/target columns are not model inputs",
    )
    try:
        frame = pd.read_csv(
            paths["dataset"], dtype={"row_id": str, "group_id": str, "time_id": str, "channel": str}
        )
    except (OSError, ValueError) as exc:
        raise ValueError("invalid dataset") from exc
    _require(
        {"row_id", "group_id", "time_id", "outcome", "channel", *features} <= set(frame.columns),
        "missing dataset columns",
    )
    _ids(frame["row_id"].tolist())
    _require(
        not frame[["group_id", "time_id", "channel", "outcome"]].isna().any().any(),
        "missing identity or label",
    )
    _require(frame["outcome"].isin([0, 1]).all(), "nonbinary outcome")
    frame = frame.set_index("row_id", drop=False)
    split = _object(_read(paths["split"]))
    test_ids = _check_splits(frame, split)
    report = _study(root, manifest, frame, split, config)
    predictions = _object(_read(paths["predictions"]))
    identity = {key: manifest[key] for key in ("dataset_sha256", "split_sha256", "config_sha256")}
    _require(predictions.get("identity") == identity, "prediction identity differs")
    rows: Any = predictions.get("rows")
    _require(isinstance(rows, list) and len(rows) == len(test_ids), "prediction count differs")
    _require(all(isinstance(row, dict) for row in rows), "invalid prediction rows")
    _require([row.get("row_id") for row in rows] == test_ids, "prediction IDs differ")
    analysis = _object(manifest.get("analysis"))
    _require(analysis.get("status") == "REQUIRES_REVIEW", "human review remains required")
    _require(
        all(
            isinstance(analysis.get(k), str) and analysis[k].strip()
            for k in ("comparison", "conclusion")
        ),
        "missing analysis",
    )
    versions, code = _object(manifest.get("versions")), _object(manifest.get("code"))
    _require(
        all(isinstance(versions.get(k), str) and versions[k] for k in ("python", "sklearn")),
        "missing versions",
    )
    _require(
        isinstance(code.get("revision"), str)
        and bool(code["revision"])
        and type(code.get("dirty")) is bool,
        "missing code identity",
    )
    digest = code.get("diff_sha256")
    _require(
        isinstance(digest, str)
        and len(digest) == 64
        and all(c in "0123456789abcdef" for c in digest),
        "invalid code diff digest",
    )
    _require(
        trusted_model_path is not None
        and trusted_model_path.is_absolute()
        and trusted_model_path.resolve() == paths["model"],
        "explicit trust in this exact absolute local model path is required",
    )
    # Recheck the exact bytes subsequently deserialized, avoiding a hash/load race.
    data = paths["model"].read_bytes()
    _require(hashlib.sha256(data).hexdigest() == manifest["model_sha256"], "model hash changed")
    try:
        bundle = _object(pickle.loads(data))
        _require(bundle.get("identity") == identity, "model identity differs")
        model: Any = bundle.get("model")
        _require(isinstance(model, Pipeline), "model must be a locally fitted sklearn Pipeline")
        _require(np.array_equal(model.classes_, [0, 1]), "model class order must be [0, 1]")
        holdout = frame.loc[test_ids]
        raw = np.asarray(model.predict(holdout[features]))
        proba = np.asarray(model.predict_proba(holdout[features]), dtype=np.float64)
    except Exception as exc:
        raise ValueError("trusted model could not replay inference") from exc
    _require(
        raw.shape == (len(test_ids),) and proba.shape == (len(test_ids), 2),
        "invalid model output shape",
    )
    _require(
        np.isfinite(proba).all()
        and ((proba >= 0) & (proba <= 1)).all()
        and np.allclose(proba.sum(axis=1), 1),
        "invalid model probabilities",
    )
    _require(np.isin(raw, [0, 1]).all(), "invalid model predictions")
    probability = proba[:, 1]
    decision = (probability >= threshold).astype(int)
    labels = holdout["outcome"].to_numpy(dtype=int)
    for i, row in enumerate(rows):
        for key, actual in (
            ("label", int(labels[i])),
            ("probability", float(probability[i])),
            ("prediction", int(raw[i])),
            ("decision", int(decision[i])),
        ):
            _same(actual, row.get(key))
    _same(
        _metrics(labels, probability, decision, holdout["channel"].to_numpy()),
        manifest.get("metrics"),
    )
    _check_report(report, manifest, labels, probability, decision, holdout["channel"].to_numpy())


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay your explicitly trusted local pipeline")
    parser.add_argument("root", type=Path)
    parser.add_argument(
        "--trust-local-model",
        type=Path,
        required=True,
        help="absolute path to your own model.pkl; pickle executes Python",
    )
    args = parser.parse_args()
    validate_evidence(args.root, trusted_model_path=args.trust_local_model)
    print("REPLAY_VERIFIED; analysis/provenance: REQUIRES_REVIEW")


if __name__ == "__main__":
    main()
