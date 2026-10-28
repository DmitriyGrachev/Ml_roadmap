"""Two fixed instructor experiments, not a solution to the support tabular study.

No downloads, student imports, arbitrary pickle loading, or implicit plotting.
Run with --output NEW_DIRECTORY; see theory.md before interpreting the numbers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from numpy.typing import NDArray
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor


@dataclass
class Experiment:
    """Fixed teacher data and its measured result; not a learner evidence schema."""

    scenario: str
    data: pd.DataFrame
    features: list[str]
    splits: dict[str, list[str]]
    model: Any
    predictions: pd.DataFrame
    report: dict[str, Any]


def cycling_data(*, seed: int) -> pd.DataFrame:
    """96 independent fictional rides; measurements available before departure."""
    rng = np.random.default_rng(seed)
    distance = rng.uniform(1, 20, 96)
    climb = rng.uniform(0, 300, 96)
    gravel = rng.integers(0, 2, 96)
    duration = 5 + 2.8 * distance + 0.025 * climb + 3 * gravel + rng.normal(0, 3, 96)
    frame = pd.DataFrame(
        {
            "distance_km": distance,
            "climb_m": climb,
            "surface": np.where(gravel, "gravel", "paved"),
            "target": duration,
        },
        index=pd.Index([f"ride-{i:03}" for i in range(96)], name="row_id"),
    )
    frame.loc[frame.index[::13], "climb_m"] = np.nan
    return frame


def sensors_data(*, seed: int) -> pd.DataFrame:
    """Extend the existing vibration/temperature teacher context with noisy labels.

    Each row is a different fictional machine, NOT repeated readings of one device.
    The older 40/80-row sensor examples are separate cohorts, not these data.
    """
    rng = np.random.default_rng(seed)
    vibration = rng.uniform(0, 10, 160)
    temperature = rng.normal(30, 5, 160)
    probability = 1 / (1 + np.exp(-((vibration - 5) * 0.9 + (temperature - 30) * 0.1)))
    frame = pd.DataFrame(
        {
            "vibration_mm_s": vibration,
            "temperature_c": temperature,
            "target": (rng.random(160) < probability).astype(int),
        },
        index=pd.Index([f"machine-{i:03}" for i in range(160)], name="row_id"),
    )
    frame.loc[frame.index[::17], "temperature_c"] = np.nan
    return frame


def split_rows(data: pd.DataFrame, *, seed: int, classification: bool) -> dict[str, list[str]]:
    """Fixed independent-unit teaching protocol; not a generic group splitter."""
    development, test = train_test_split(
        data.index.tolist(),
        test_size=0.2,
        random_state=seed,
        stratify=data.target if classification else None,
    )
    train, validation = train_test_split(
        development,
        test_size=0.375 if classification else 0.25,
        random_state=seed + 1,
        stratify=data.loc[development, "target"] if classification else None,
    )
    parts = {"train": train, "validation": validation, "test": test}
    if classification:
        validation, calibration = train_test_split(
            validation,
            test_size=0.5,
            random_state=seed + 2,
            stratify=data.loc[validation, "target"],
        )
        parts.update(validation=validation, calibration=calibration)
    return parts


def predict_checked(
    model: Any, frame: pd.DataFrame, features: list[str], *, scenario: str
) -> NDArray[np.float64]:
    """Inference accepts the same ordered raw feature columns, never the target."""
    if frame.columns.tolist() != features:
        raise ValueError(f"feature schema must be {features}, in that order")
    values = model.predict_proba(frame)[:, 1] if scenario == "sensors" else model.predict(frame)
    return np.asarray(values, dtype=np.float64)


def cycling_experiment(*, seed: int = 31) -> Experiment:
    data = cycling_data(seed=seed)
    features = ["distance_km", "climb_m", "surface"]
    splits = split_rows(data, seed=seed, classification=False)
    train, val, test = (data.loc[splits[part]] for part in ("train", "validation", "test"))
    candidates: list[tuple[str, Any, dict[str, Any]]] = [
        ("baseline", DummyRegressor(strategy="mean"), {"family": "baseline"})
    ]
    for alpha in (0.1, 10.0):
        candidates.append(
            (f"ridge-{alpha}", Ridge(alpha=alpha), {"family": "ridge", "alpha": alpha})
        )
    for depth in (1, 3, 8):
        candidates.append(
            (
                f"tree-{depth}",
                DecisionTreeRegressor(max_depth=depth, min_samples_leaf=3, random_state=seed),
                {"family": "tree", "depth": depth},
            )
        )
    runs, fitted = [], {}
    for name, estimator, config in candidates:
        # A new unfitted transformer for each candidate, fit ONLY on train.
        transform = ColumnTransformer(
            [
                (
                    "numeric",
                    make_pipeline(SimpleImputer(strategy="median"), StandardScaler()),
                    ["distance_km", "climb_m"],
                ),
                (
                    "surface",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    ["surface"],
                ),
            ]
        )
        model = make_pipeline(transform, estimator)
        model.fit(train[features], train.target)
        runs.append(
            {
                "name": name,
                **config,
                "train_mae": float(
                    mean_absolute_error(train.target, model.predict(train[features]))
                ),
                "validation_mae": float(
                    mean_absolute_error(val.target, model.predict(val[features]))
                ),
            }
        )
        fitted[name] = model
    selected = min(runs, key=lambda row: (row["validation_mae"], row["name"]))
    # Selection is now frozen. No refit or feedback from test into the experiment.
    model = fitted[selected["name"]]
    predicted = predict_checked(model, test[features], features, scenario="cycling")
    rows = pd.DataFrame(
        {
            "row_id": test.index,
            "group": test.surface.to_numpy(),
            "target": test.target.to_numpy(),
            "prediction": predicted,
            "baseline_prediction": fitted["baseline"].predict(test[features]),
        }
    )
    mse = float(mean_squared_error(rows.target, rows.prediction))
    report = {
        "selection": {"name": selected["name"], "criterion": "validation MAE; name breaks ties"},
        "development": runs,
        "test_metrics": {
            "count": len(rows),
            "mae_minutes": float(mean_absolute_error(rows.target, rows.prediction)),
            "mse_minutes_squared": mse,
            "rmse_minutes": float(np.sqrt(mse)),
            "baseline_mae_minutes": float(
                mean_absolute_error(rows.target, rows.baseline_prediction)
            ),
        },
        "error_slices": {
            str(name): {
                "count": len(group),
                "mae_minutes": float(mean_absolute_error(group.target, group.prediction)),
            }
            for name, group in rows.groupby("group")
        },
    }
    return Experiment("cycling", data, features, splits, model, rows, report)


def sensors_experiment(*, seed: int = 31) -> Experiment:
    data = sensors_data(seed=seed)
    features = ["vibration_mm_s", "temperature_c"]
    splits = split_rows(data, seed=seed, classification=True)
    train, val, calibration, test = (
        data.loc[splits[part]] for part in ("train", "validation", "calibration", "test")
    )
    runs, fitted = [], {}
    for c in (0.1, 1.0):
        model = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(C=c, random_state=seed, max_iter=500),
        )
        model.fit(train[features], train.target)
        runs.append(
            {
                "C": c,
                "brier": float(
                    brier_score_loss(val.target, model.predict_proba(val[features])[:, 1])
                ),
            }
        )
        fitted[c] = model
    selected = min(runs, key=lambda row: (row["brier"], row["C"]))
    raw = fitted[selected["C"]]
    calibrated = CalibratedClassifierCV(FrozenEstimator(raw), method="sigmoid")
    calibrated.fit(calibration[features], calibration.target)
    choices = [("raw", raw), ("sigmoid", calibrated)]
    calibration_scores = {
        name: float(brier_score_loss(val.target, candidate.predict_proba(val[features])[:, 1]))
        for name, candidate in choices
    }
    calibration_name, final_model = min(
        choices, key=lambda item: (calibration_scores[item[0]], item[0])
    )
    probabilities = final_model.predict_proba(val[features])[:, 1]
    thresholds = []
    for threshold in (0.3, 0.5, 0.7):
        decision = probabilities >= threshold
        fp = int(np.sum(decision & (val.target.to_numpy() == 0)))
        fn = int(np.sum(~decision & (val.target.to_numpy() == 1)))
        thresholds.append({"threshold": threshold, "fp": fp, "fn": fn, "cost": fp + 4 * fn})
    policy = min(thresholds, key=lambda row: (row["cost"], row["threshold"]))
    # All choices are frozen, including the error costs and the explicit tie rule.
    baseline = DummyClassifier(strategy="prior").fit(train[features], train.target)
    importance = permutation_importance(
        final_model,
        val[features],
        val.target,
        scoring="neg_brier_score",
        n_repeats=5,
        random_state=seed,
        n_jobs=1,
    )
    probability = predict_checked(final_model, test[features], features, scenario="sensors")
    decision = (probability >= policy["threshold"]).astype(int)
    rows = pd.DataFrame(
        {
            "row_id": test.index,
            "group": np.where(test.vibration_mm_s >= 5, "high-vibration", "low-vibration"),
            "target": test.target.to_numpy(),
            "probability": probability,
            "decision": decision,
            "baseline_probability": baseline.predict_proba(test[features])[:, 1],
        }
    )
    matrix = confusion_matrix(rows.target, decision, labels=[0, 1])
    report = {
        "selection": {
            "C": selected["C"],
            "calibration": calibration_name,
            "threshold": policy["threshold"],
            "false_positive_cost": 1,
            "false_negative_cost": 4,
            "criterion": (
                "validation Brier then validation cost; lower C/raw/lower threshold on ties"
            ),
        },
        "development": {"raw_candidates": runs, "calibration_brier": calibration_scores},
        "thresholds": thresholds,
        "permutation_importance_validation": {
            "features": features,
            "brier_increase_mean": importance.importances_mean.tolist(),
            "brier_increase_std": importance.importances_std.tolist(),
            "repeats": 5,
        },
        "test_metrics": {
            "count": len(rows),
            "confusion": matrix.tolist(),
            "accuracy": float(accuracy_score(rows.target, decision)),
            "precision": float(precision_score(rows.target, decision, zero_division=0)),
            "recall": float(recall_score(rows.target, decision, zero_division=0)),
            "f1": float(f1_score(rows.target, decision, zero_division=0)),
            "roc_auc": float(roc_auc_score(rows.target, probability)),
            "average_precision": float(average_precision_score(rows.target, probability)),
            "brier": float(brier_score_loss(rows.target, probability)),
            "baseline_brier": float(brier_score_loss(rows.target, rows.baseline_probability)),
            "cost": int(matrix[0, 1] + 4 * matrix[1, 0]),
        },
        "error_slices": {
            str(name): {
                "count": len(group),
                "fp": int(((group.decision == 1) & (group.target == 0)).sum()),
                "fn": int(((group.decision == 0) & (group.target == 1)).sum()),
                "brier": float(brier_score_loss(group.target, group.probability)),
            }
            for name, group in rows.groupby("group")
        },
    }
    return Experiment("sensors", data, features, splits, final_model, rows, report)


def export_experiment(experiment: Experiment, directory: Path, *, seed: int) -> Path:
    """Write and reload ONLY the trusted object constructed by this invocation.

    Pickle is executable: a checksum detects changed bytes but cannot establish trust.
    This is not an API for opening downloaded or student-supplied model files.
    """
    directory.mkdir(parents=True, exist_ok=False)
    payload = pickle.dumps({"model": experiment.model, "features": experiment.features})
    files = {
        "data.csv": experiment.data.to_csv(lineterminator="\n").encode("utf-8"),
        "predictions.csv": experiment.predictions.to_csv(index=False, lineterminator="\n").encode(
            "utf-8"
        ),
        "model.pkl": payload,
    }
    for name, content in files.items():
        (directory / name).write_bytes(content)
    saved = (directory / "model.pkl").read_bytes()
    if saved != payload:
        raise ValueError("our newly written model bytes changed; refusing reload")
    restored = pickle.loads(saved)
    x = experiment.data.loc[experiment.splits["test"], experiment.features]
    actual = predict_checked(
        restored["model"], x, restored["features"], scenario=experiment.scenario
    )
    column = "probability" if experiment.scenario == "sensors" else "prediction"
    np.testing.assert_array_equal(actual, experiment.predictions[column])
    report = {
        "kind": "INSTRUCTOR_SYNTHETIC_DEMO_NOT_LEARNER_EVIDENCE",
        "seed": seed,
        "scenario": experiment.scenario,
        "splits": experiment.splits,
        "schema": {name: str(experiment.data[name].dtype) for name in experiment.features},
        "features": experiment.features,
        "feature_units": (
            {"vibration_mm_s": "mm/s", "temperature_c": "degrees C"}
            if experiment.scenario == "sensors"
            else {"distance_km": "km", "climb_m": "m", "surface": "paved/gravel"}
        ),
        "target_classes": [0, 1] if experiment.scenario == "sensors" else None,
        # Human-readable configuration; fitted coefficients/statistics live in model.pkl.
        "estimator_parameters": {
            name: (
                value
                if isinstance(value, (str, int, float, bool, type(None)))
                and not (isinstance(value, float) and not np.isfinite(value))
                else repr(value)
            )
            for name, value in experiment.model.get_params(deep=True).items()
        },
        "target": "maintenance within next day: 0/1"
        if experiment.scenario == "sensors"
        else "duration in minutes",
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "sklearn": sklearn.__version__,
        },
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sha256": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
        "reloaded_predictions_equal": True,
        **experiment.report,
    }
    path = directory / "report.json"
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return path


def make_figures(cycling: Experiment, sensors: Experiment) -> dict[str, Any]:
    """Optional measured plots; imports stay out of the numerical learning path."""
    import matplotlib.pyplot as plt

    complexity, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    trees = [row for row in cycling.report["development"] if row["family"] == "tree"]
    for key, label in (("train_mae", "train"), ("validation_mae", "validation")):
        axes[0].plot(
            [row["depth"] for row in trees], [row[key] for row in trees], "o-", label=label
        )
    axes[0].set(
        xlabel="Maximum tree depth", ylabel="MAE (minutes)", title="Complexity, not training size"
    )
    axes[0].legend()
    residual = cycling.predictions.prediction - cycling.predictions.target
    axes[1].hist(residual, bins=6, edgecolor="white")
    axes[1].set(
        xlabel="Prediction - actual (minutes)",
        ylabel="Test rides (count)",
        title="Frozen selected model",
    )
    decisions, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    trace = sensors.report["thresholds"]
    axes[0].plot([row["threshold"] for row in trace], [row["cost"] for row in trace], "o-")
    axes[0].set(
        xlabel="Decision threshold",
        ylabel="Validation cost (FP + 4 FN)",
        title="Policy selection on 24 rows",
    )
    matrix = np.asarray(sensors.report["test_metrics"]["confusion"])
    axes[1].imshow(matrix, cmap="Blues", vmin=0)
    for (i, j), value in np.ndenumerate(matrix):
        axes[1].text(
            j,
            i,
            str(value),
            ha="center",
            va="center",
            color="black",
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
        )
    axes[1].set(
        xticks=[0, 1],
        yticks=[0, 1],
        xlabel="Decision",
        ylabel="True label",
        title="Frozen policy: test counts",
    )
    return {"complexity": complexity, "decisions": decisions}


def run_demo(output: Path, *, seed: int = 31, plots: bool = False) -> Path:
    output.mkdir(parents=True, exist_ok=False)
    cycling, sensors = cycling_experiment(seed=seed), sensors_experiment(seed=seed)
    for experiment in (cycling, sensors):
        export_experiment(experiment, output / experiment.scenario, seed=seed)
    if plots:
        import matplotlib.pyplot as plt

        for name, figure in make_figures(cycling, sensors).items():
            try:
                figure.savefig(output / f"{name}.png", dpi=150)
            finally:
                plt.close(figure)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    destination = run_demo(args.output, seed=args.seed, plots=args.plots)
    print(f"Instructor results (not learner credit): {destination}")
    for case in ("cycling", "sensors"):
        result = json.loads((destination / case / "report.json").read_text(encoding="utf-8"))
        print(case, json.dumps(result["selection"], ensure_ascii=False))
        print(json.dumps(result["test_metrics"], ensure_ascii=False))
