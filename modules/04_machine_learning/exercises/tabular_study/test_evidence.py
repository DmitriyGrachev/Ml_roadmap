"""Reject stale or inconsistent claims, even when individual files are rehashed."""

import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from .evidence import validate_evidence


def save(root: Path, name: str, value: object) -> str:
    data = json.dumps(value, sort_keys=True, allow_nan=False).encode()
    (root / name).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    """Test-only, hand-computable estimator; not a completed learner study."""
    rows = [
        {
            "row_id": f"r{i}",
            "group_id": f"g{i // 2}",
            "time_id": i,
            "channel": "a" if i % 2 else "b",
            "x": i,
            "outcome": i % 2,
        }
        for i in range(16)
    ]
    pd.DataFrame(rows).to_csv(tmp_path / "dataset.csv", index=False)
    dev = [f"r{i}" for i in range(12)]
    split: dict[str, Any] = {
        "development_ids": dev,
        "test_ids": [f"r{i}" for i in range(12, 16)],
        "folds": [
            {
                "train_ids": [x for x in dev if x not in dev[k : k + 4]],
                "validation_ids": dev[k : k + 4],
            }
            for k in (0, 4, 8)
        ],
    }
    config: dict[str, Any] = {
        "seed": 7,
        "features": ["x"],
        "threshold": 0.5,
        "selected_id": "dummy",
        "candidates": [
            {"id": "dummy", "family": "Dummy", "calibration": "raw", "feature_set": "base"},
            {
                "id": "linear",
                "family": "LogisticRegression",
                "calibration": "raw",
                "feature_set": "added",
            },
            {
                "id": "calibrated",
                "family": "LogisticRegression",
                "calibration": "sigmoid",
                "feature_set": "added",
            },
            {
                "id": "ablated",
                "family": "LogisticRegression",
                "calibration": "raw",
                "feature_set": "base",
            },
            {
                "id": "tree",
                "family": "TreeOrRandomForest",
                "calibration": "raw",
                "feature_set": "base",
            },
            {
                "id": "boost",
                "family": "HistGradientBoostingClassifier",
                "calibration": "raw",
                "feature_set": "base",
            },
        ],
        "reruns": 0,
        "elapsed_seconds": 0.1,
    }
    dataset_sha = hashlib.sha256((tmp_path / "dataset.csv").read_bytes()).hexdigest()
    split_sha = save(tmp_path, "split.json", split)
    config_sha = save(tmp_path, "config.json", config)
    identity = {
        "dataset_sha256": dataset_sha,
        "split_sha256": split_sha,
        "config_sha256": config_sha,
    }
    model = Pipeline([("classifier", DummyClassifier(strategy="prior"))])
    model.fit(pd.DataFrame(rows[:12])[["x"]], [i % 2 for i in range(12)])
    (tmp_path / "model.pkl").write_bytes(pickle.dumps({"identity": identity, "model": model}))
    predictions = {
        "identity": identity,
        "rows": [
            {"row_id": f"r{i}", "label": i % 2, "probability": 0.5, "prediction": 0, "decision": 1}
            for i in range(12, 16)
        ],
    }
    metrics = {
        "count": 4,
        "accuracy": 0.5,
        "brier": 0.25,
        "log_loss": 0.6931471805599453,
        "fp": 2,
        "fn": 0,
        "reliability": [
            {
                "lower": 0.0,
                "upper": 0.5,
                "count": 0,
                "mean_probability": None,
                "positive_rate": None,
            },
            {"lower": 0.5, "upper": 1.0, "count": 4, "mean_probability": 0.5, "positive_rate": 0.5},
        ],
        "slices": {"a": {"count": 2, "fp": 0, "fn": 0}, "b": {"count": 2, "fp": 2, "fn": 0}},
    }
    # These are hand-computable validator inputs, not six trained study models.
    study = {
        "runs": [
            {
                "config_id": candidate["id"],
                "fold_id": fold_id,
                "predictions": [
                    {"row_id": row_id, "probability": 0.5}
                    for row_id in split["folds"][fold_id]["validation_ids"]
                ],
                "brier": 0.25,
                "log_loss": 0.6931471805599453,
            }
            for candidate in config["candidates"]
            for fold_id in range(3)
        ],
        "calibration": {
            "raw": "linear",
            "sigmoid": "calibrated",
            "reliability": {
                name: [
                    {
                        "lower": 0.0,
                        "upper": 0.5,
                        "count": 0,
                        "mean_probability": None,
                        "positive_rate": None,
                    },
                    {
                        "lower": 0.5,
                        "upper": 1.0,
                        "count": 12,
                        "mean_probability": 0.5,
                        "positive_rate": 0.5,
                    },
                ]
                for name in ("raw", "sigmoid")
            },
        },
        "ablation": {
            "with_feature": "linear",
            "without_feature": "ablated",
            "feature": "test-only-derived-feature",
            "availability": "test fixture",
        },
        "permutation_importance": {
            "config_id": "linear",
            "fold_id": 0,
            "feature": "x",
            "predictions": [{"row_id": f"r{i}", "probability": 0.5} for i in range(4)],
            "brier_increase": 0.0,
        },
        "paired_comparison": {"config_a": "dummy", "config_b": "linear"},
        "evaluation_report": {
            "schema_version": 1,
            "model_name": "dummy",
            "versions": {"python": "test", "numpy": "test", "scikit_learn": "test"},
            "threshold": 0.5,
            "seed": 7,
            "dataset_sha256": dataset_sha,
            "slices": {
                "a": {
                    "count": 2,
                    "accuracy": 1.0,
                    "precision": 1.0,
                    "recall": 1.0,
                    "f1": 1.0,
                    "brier": 0.25,
                },
                "b": {
                    "count": 2,
                    "accuracy": 0.0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "brier": 0.25,
                },
            },
            "metrics": {
                "count": 4,
                "accuracy": 0.5,
                "precision": 0.5,
                "recall": 1.0,
                "f1": 2 / 3,
                "brier": 0.25,
            },
        },
    }
    paired = tmp_path / "paired"
    paired.mkdir()
    paired_manifest = {
        "schema_version": 1,
        "exercise_id": "data-paired-model-comparison",
        "dataset_sha256": save(
            paired,
            "snapshot.json",
            [{"row_id": f"r{i}", "unit_id": f"g{i // 2}", "label": i % 2} for i in range(12)],
        ),
        "split_sha256": save(paired, "split.json", {"evaluation_row_ids": dev}),
        "predictions_sha256": save(
            paired,
            "predictions.json",
            [
                {
                    "row_id": f"r{i}",
                    "prediction_a": 0.5,
                    "prediction_b": 0.5,
                    "loss_a": 0.25,
                    "loss_b": 0.25,
                }
                for i in range(12)
            ],
        ),
        "resamples_sha256": save(
            paired,
            "resamples.json",
            {
                "unit_ids": [f"g{i}" for i in range(6)],
                "indices": np.random.default_rng(7).integers(0, 6, (100, 6)).tolist(),
            },
        ),
        "config": {
            "seed": 7,
            "n_resamples": 100,
            "confidence": 0.95,
            "unit_policy": "cluster_by_unit_id",
            "loss": "squared_error",
        },
        "effect": 0.0,
        "lower": 0.0,
        "upper": 0.0,
        "unit_count": 6,
        "resample_count": 100,
    }
    paired_sha = save(paired, "manifest.json", paired_manifest)
    manifest = {
        "schema_version": 1,
        "exercise_id": "ml-tabular-study",
        **identity,
        "config": config,
        "model_sha256": hashlib.sha256((tmp_path / "model.pkl").read_bytes()).hexdigest(),
        "predictions_sha256": save(tmp_path, "predictions.json", predictions),
        "study_sha256": save(tmp_path, "study.json", study),
        "paired_sha256": paired_sha,
        "metrics": metrics,
        "versions": {"python": "test", "sklearn": "test"},
        "code": {"revision": "test-local", "dirty": True, "diff_sha256": "a" * 64},
        "analysis": {
            "status": "REQUIRES_REVIEW",
            "comparison": "test fixture only",
            "conclusion": "No scientific conclusion in this infrastructure fixture",
        },
    }
    save(tmp_path, "manifest.json", manifest)
    return tmp_path


def read(root: Path, name: str) -> Any:
    return json.loads((root / name).read_text())


def test_real_estimator_replay_is_read_only(evidence_root: Path) -> None:
    before = {str(p): p.read_bytes() for p in evidence_root.rglob("*") if p.is_file()}
    validate_evidence(evidence_root, trusted_model_path=evidence_root / "model.pkl")
    assert before == {str(p): p.read_bytes() for p in evidence_root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("location", ["external", "root_link", "model_link"])
def test_student_trust_boundary_rejects_redirect_before_replay(
    evidence_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, location: str
) -> None:
    import shutil

    from . import test_starter as contract

    data = tmp_path / "input.csv"
    data.write_bytes((evidence_root / "dataset.csv").read_bytes())
    output = tmp_path / "fresh"
    replayed: list[Path] = []

    def directory_link(link: Path, target: Path) -> None:
        if sys.platform == "win32":
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                check=True,
                capture_output=True,
            )
        else:
            link.symlink_to(target, target_is_directory=True)

    def redirect(data_path: Path, output_dir: Path, *, seed: int) -> Path:
        if location == "external":
            return evidence_root / "manifest.json"
        if location == "root_link":
            directory_link(output_dir, evidence_root)
        else:
            shutil.copytree(evidence_root, output_dir, ignore=shutil.ignore_patterns("fresh"))
            # A directory at model.pkl is deliberately not a pickle; no payload executes.
            (output_dir / "model.pkl").rename(output_dir / "unused-model.pkl")
            directory_link(output_dir / "model.pkl", evidence_root)
        return output_dir / "manifest.json"

    def replay(root: Path, *, trusted_model_path: Path) -> None:
        replayed.append(trusted_model_path)

    monkeypatch.setattr(contract, "run_experiment", redirect)
    monkeypatch.setattr(contract, "validate_evidence", replay)
    with pytest.raises(AssertionError, match=r"fresh output|model"):
        contract.check_study(data, output, seed=7)
    assert replayed == []


@pytest.mark.parametrize("change_input", [False, True])
def test_student_contract_binds_supplied_dataset_before_run(
    evidence_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change_input: bool
) -> None:
    import shutil

    from . import test_starter as contract

    data = tmp_path / "supplied.csv"
    supplied = pd.read_csv(evidence_root / "dataset.csv")
    supplied.loc[0, "x"] = 999
    supplied.to_csv(data, index=False)
    # The saved study is internally consistent and replays; only input identity differs.
    validate_evidence(evidence_root, trusted_model_path=evidence_root / "model.pkl")

    def other_study(data_path: Path, output_dir: Path, *, seed: int) -> Path:
        shutil.copytree(evidence_root, output_dir, ignore=shutil.ignore_patterns("fresh"))
        if change_input:
            data_path.write_bytes((output_dir / "dataset.csv").read_bytes())
        return output_dir / "manifest.json"

    replayed: list[Path] = []

    def replay(root: Path, *, trusted_model_path: Path) -> None:
        replayed.append(trusted_model_path)

    monkeypatch.setattr(contract, "run_experiment", other_study)
    monkeypatch.setattr(contract, "validate_evidence", replay)
    with pytest.raises(AssertionError, match=r"input|dataset"):
        contract.check_study(data, tmp_path / "fresh", seed=7)
    assert replayed == []


@pytest.mark.parametrize("trust", [None, "sibling.pkl", "../model.pkl"])
def test_no_implicit_or_other_file_trust(evidence_root: Path, trust: str | None) -> None:
    path = None if trust is None else evidence_root / trust
    with pytest.raises(ValueError, match="trust"):
        validate_evidence(evidence_root, trusted_model_path=path)


@pytest.mark.parametrize(
    "mutation",
    [
        "group",
        "split",
        "fold",
        "id",
        "checksum",
        "config",
        "metric",
        "probability",
        "prediction",
        "label",
        "decision",
        "model_missing",
        "model_corrupt",
        "stale_model",
        "budget",
        "review",
        "duplicate",
        "reliability",
        "slice",
    ],
)
def test_tampering_is_rejected(evidence_root: Path, mutation: str) -> None:
    root = evidence_root
    manifest = read(root, "manifest.json")
    if mutation == "group":
        frame = pd.read_csv(root / "dataset.csv")
        frame.loc[12, "group_id"] = "g0"
        frame.to_csv(root / "dataset.csv", index=False)
        manifest["dataset_sha256"] = hashlib.sha256((root / "dataset.csv").read_bytes()).hexdigest()
    elif mutation in {"split", "fold"}:
        split = read(root, "split.json")
        if mutation == "split":
            split["test_ids"][0] = "r0"
        else:
            split["folds"][0]["train_ids"][0] = "r0"
        manifest["split_sha256"] = save(root, "split.json", split)
    elif mutation in {"id", "probability", "prediction", "label", "decision", "duplicate"}:
        predictions = read(root, "predictions.json")
        key = "row_id" if mutation in {"id", "duplicate"} else mutation
        predictions["rows"][0][key] = {
            "id": "r0",
            "duplicate": "r13",
            "probability": 0.7,
            "prediction": 1,
            "label": 1,
            "decision": 0,
        }[mutation]
        manifest["predictions_sha256"] = save(root, "predictions.json", predictions)
    elif mutation == "checksum":
        manifest["dataset_sha256"] = "0" * 64
    elif mutation == "config":
        manifest["config"]["threshold"] = 0.8
    elif mutation == "budget":
        manifest["config"]["candidates"] *= 13
        manifest["config_sha256"] = save(root, "config.json", manifest["config"])
    elif mutation == "review":
        manifest["analysis"]["status"] = "PASSED"
    elif mutation == "metric":
        manifest["metrics"]["brier"] = 0.1
    elif mutation == "reliability":
        manifest["metrics"]["reliability"][1]["count"] = 3
    elif mutation == "slice":
        manifest["metrics"]["slices"]["b"]["fp"] = 0
    elif mutation == "model_missing":
        (root / "model.pkl").rename(root / "missing-model.pkl")
    elif mutation == "model_corrupt":
        (root / "model.pkl").write_bytes(b"not a pickle")
        manifest["model_sha256"] = hashlib.sha256(b"not a pickle").hexdigest()
    else:
        stale = Pipeline([("classifier", DummyClassifier(strategy="constant", constant=1))])
        stale.fit(pd.DataFrame({"x": [0, 1]}), [0, 1])
        identity = read(root, "predictions.json")["identity"]
        data = pickle.dumps({"identity": identity, "model": stale})
        (root / "model.pkl").write_bytes(data)
        manifest["model_sha256"] = hashlib.sha256(data).hexdigest()
    save(root, "manifest.json", manifest)
    reason = {
        "group": "group membership",
        "split": "membership",
        "fold": "fold membership",
        "config": "config differs",
        "metric": "metric differs",
    }.get(mutation, r".")
    with pytest.raises(ValueError, match=reason):
        validate_evidence(root, trusted_model_path=root / "model.pkl")


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "metric",
        "fold",
        "row",
        "calibration",
        "ablation",
        "importance",
        "paired",
        "report",
        "family",
        "report_slice",
        "selection",
        "calibration_bins",
    ],
)
def test_review_artifacts_require_real_cross_linked_results(
    evidence_root: Path, mutation: str
) -> None:
    root = evidence_root
    manifest, study = read(root, "manifest.json"), read(root, "study.json")
    if mutation == "missing":
        (root / "study.json").rename(root / "absent-study.json")
    elif mutation == "metric":
        study["runs"][0]["brier"] = 0.01
    elif mutation == "fold":
        study["runs"][0]["fold_id"] = 9
    elif mutation == "row":
        study["runs"][0]["predictions"][0]["row_id"] = "r12"
    elif mutation == "calibration":
        study["calibration"]["sigmoid"] = "tree"
    elif mutation == "ablation":
        study["ablation"]["without_feature"] = "linear"
    elif mutation == "importance":
        study["permutation_importance"]["brier_increase"] = 0.1
    elif mutation == "paired":
        study["paired_comparison"]["config_b"] = "missing-model"
    elif mutation == "report":
        study["evaluation_report"]["metrics"]["precision"] = 1.0
    elif mutation == "report_slice":
        study["evaluation_report"]["slices"]["a"]["brier"] = 0.0
    elif mutation == "selection":
        study["evaluation_report"]["model_name"] = "unknown"
    elif mutation == "calibration_bins":
        study["calibration"]["reliability"]["sigmoid"][1]["count"] = 11
    else:
        manifest["config"]["candidates"][-1]["family"] = "TreeOrRandomForest"
        manifest["config_sha256"] = save(root, "config.json", manifest["config"])
        identity = {k: manifest[k] for k in ("dataset_sha256", "split_sha256", "config_sha256")}
        predictions = read(root, "predictions.json")
        predictions["identity"] = identity
        manifest["predictions_sha256"] = save(root, "predictions.json", predictions)
        bundle = pickle.loads((root / "model.pkl").read_bytes())
        bundle["identity"] = identity
        data = pickle.dumps(bundle)
        (root / "model.pkl").write_bytes(data)
        manifest["model_sha256"] = hashlib.sha256(data).hexdigest()
    if mutation != "missing":
        manifest["study_sha256"] = save(root, "study.json", study)
    save(root, "manifest.json", manifest)
    with pytest.raises(ValueError, match=r"."):
        validate_evidence(root, trusted_model_path=root / "model.pkl")


def test_evidence_cli_requires_trust_and_reports_review_separately(evidence_root: Path) -> None:
    command = [
        sys.executable,
        "-m",
        "modules.04_machine_learning.exercises.tabular_study.evidence",
        str(evidence_root),
    ]
    denied = subprocess.run(command, capture_output=True, text=True, check=False)
    assert denied.returncode == 2
    assert "--trust-local-model" in denied.stderr
    allowed = subprocess.run(
        [*command, "--trust-local-model", str(evidence_root / "model.pkl")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert allowed.returncode == 0, allowed.stderr
    assert "REPLAY_VERIFIED" in allowed.stdout
    assert "REQUIRES_REVIEW" in allowed.stdout


@pytest.mark.parametrize(
    ("field", "value", "missing"),
    [
        ("family", "SVC", False),
        ("family", "GradientBoostingClassifier", False),
        ("calibration", None, True),
        ("calibration", "isotonic", False),
        ("calibration", None, False),
        ("feature_set", None, True),
        ("feature_set", "", False),
        ("feature_set", "   ", False),
        ("feature_set", ["base"], False),
        ("feature_set", None, False),
    ],
)
def test_every_candidate_schema_is_checked_after_consistent_rehash(
    evidence_root: Path, field: str, value: object, missing: bool
) -> None:
    root = evidence_root
    manifest, study = read(root, "manifest.json"), read(root, "study.json")
    tree = next(c for c in manifest["config"]["candidates"] if c["id"] == "tree")
    if field == "family":
        # Preserve all four required families and append complete runs for the extra one.
        candidate = {**tree, "id": "unsupported", "family": value}
        manifest["config"]["candidates"].append(candidate)
        study["runs"].extend(
            {**run, "config_id": "unsupported"}
            for run in list(study["runs"])
            if run["config_id"] == "tree"
        )
    elif missing:
        tree.pop(field)
    else:
        tree[field] = value
    # The tree is outside calibration/ablation pairs. Only its own schema can reject this.
    manifest["study_sha256"] = save(root, "study.json", study)
    manifest["config_sha256"] = save(root, "config.json", manifest["config"])
    identity = {k: manifest[k] for k in ("dataset_sha256", "split_sha256", "config_sha256")}
    predictions = read(root, "predictions.json")
    predictions["identity"] = identity
    manifest["predictions_sha256"] = save(root, "predictions.json", predictions)
    bundle = pickle.loads((root / "model.pkl").read_bytes())
    bundle["identity"] = identity
    data = pickle.dumps(bundle)
    (root / "model.pkl").write_bytes(data)
    manifest["model_sha256"] = hashlib.sha256(data).hexdigest()
    save(root, "manifest.json", manifest)
    with pytest.raises(ValueError, match=field):
        validate_evidence(root, trusted_model_path=root / "model.pkl")
