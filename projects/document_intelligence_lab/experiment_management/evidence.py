"""Audit saved experiment identities, predictions and actual local library artifacts."""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import url2pathname

from ..artifacts import file_sha256, read_json
from ..tracking_intro.demo import require_local_artifact_uri
from .protocol import digest, macro_f1, objective_inputs, split_digest, validate_table


def required_evidence() -> Path:
    path = os.environ.get("ROADMAP_EXPERIMENT_EVIDENCE")
    if not path:
        raise NotImplementedError("Run learner search; set ROADMAP_EXPERIMENT_EVIDENCE")
    return Path(path)


def validate_report(
    report: dict[str, Any], dataset: dict[str, Any], *, learner: bool = True
) -> int:
    kind = "STUDENT_EXPERIMENT_MANAGEMENT" if learner else "AUTHOR_SYNTHETIC_EXPERIMENT_SMOKE_ONLY"
    if (
        type(report.get("schema_version")) is not int
        or report.get("schema_version") != 1
        or report.get("exercise_id") != "ml-experiment-management"
        or report.get("evidence_kind") != kind
    ):
        raise ValueError("wrong experiment identity/evidence kind")
    objective_inputs(dataset)
    if report.get("dataset_sha256") != digest(dataset) or report.get(
        "split_sha256"
    ) != split_digest(dataset):
        raise ValueError("dataset/split digest mismatch")
    if report.get("objective") != "dev_macro_f1" or report.get("direction") != "maximize":
        raise ValueError("explicit dev_macro_f1/maximize objective required")
    if type(report.get("seed")) is not int or report.get("quality_defense") != "REQUIRES_REVIEW":
        raise ValueError("explicit integer seed and human quality defense required")
    trials = report["trials"]
    selected = validate_table(
        trials,
        [row["label"] for row in dataset["dev"]],
        selected=report["selected_trial"],
        budget=report["budget"],
    )
    runs = set()
    for trial in trials:
        if trial.get("fit_ids") != [row["id"] for row in dataset["train"]]:
            raise ValueError("fit IDs must contain train only")
        if trial.get("dev_ids") != [row["id"] for row in dataset["dev"]]:
            raise ValueError("objective prediction IDs differ from dev")
        if (
            not isinstance(trial.get("params"), dict)
            or (trial["state"] == "COMPLETE" and not trial["params"])
            or not trial.get("run_id")
            or trial["run_id"] in runs
        ):
            raise ValueError("each trial needs params and a distinct MLflow run")
        runs.add(trial["run_id"])
    winner = next(row for row in trials if row["number"] == selected)
    if report.get("selected_run_id") != winner["run_id"]:
        raise ValueError("selected run differs from selected trial")
    if report.get("dev_predictions") != winner["dev_predictions"]:
        raise ValueError("selected predictions differ from validation table")
    expected = macro_f1([row["label"] for row in dataset["holdout"]], report["holdout_predictions"])
    if not math.isclose(report["holdout_macro_f1"], expected, abs_tol=1e-12):
        raise ValueError("holdout metric differs from saved predictions")
    if report.get("model_uri") != f"models:/{report.get('model_id')}":
        raise ValueError("selected model URI must pin a logged model ID")
    return selected


def validate_experiment(
    root: Path, *, learner: bool = True, trusted_local_artifact: bool = False
) -> dict[str, str]:
    """Verify real SQLite Optuna state, MLflow logs and local sklearn reload.

    Pickle loading requires explicit trust in locally generated learner bytes.
    Metadata consistency cannot prove original authorship or unseen tuning history.
    """
    root = root.resolve()
    report, dataset = read_json(root / "experiment.json"), read_json(root / "dataset.json")
    selected = validate_report(report, dataset, learner=learner)
    source = Path(__file__).with_name("starter.py" if learner else "demo.py")
    if report.get("code_sha256") != file_sha256(source):
        raise ValueError("source hash differs from selected implementation")
    if learner:
        for key in (
            "budget_bias",
            "failure_pruning",
            "holdout_policy",
            "seed_limits",
            "hf_transfer",
        ):
            if (
                not isinstance(report.get("analysis", {}).get(key), str)
                or not report["analysis"][key].strip()
            ):
                raise ValueError(f"required learner analysis missing: {key}")
        from .demo import author_dataset

        if dataset == author_dataset() or len(dataset["train"]) < 8:
            raise ValueError("independent learner domain with at least eight train rows required")
    if not trusted_local_artifact:
        raise ValueError(
            "explicit trusted_local_artifact required for local sklearn deserialization"
        )
    from .runtime import libraries, local_model_directory, local_paths, model_digest

    mlflow, optuna = libraries()
    from importlib.metadata import version

    expected_versions = {
        "mlflow": mlflow.__version__,
        "optuna": optuna.__version__,
        "sklearn": version("scikit-learn"),
        "numpy": version("numpy"),
    }
    if report.get("versions") != expected_versions:
        raise ValueError("recorded runtime versions differ from installed libraries")
    _, artifact_root, tracking_uri, _ = local_paths(root)
    # Never create a missing store and accidentally turn absent evidence into an empty run.
    if not (root / "runs.sqlite").is_file() or not (root / "study.sqlite").is_file():
        raise ValueError("saved local SQLite stores required")
    client = mlflow.MlflowClient(tracking_uri=tracking_uri, registry_uri=tracking_uri)
    study = optuna.load_study(
        study_name=report["study_name"], storage="sqlite:///" + (root / "study.sqlite").as_posix()
    )
    if study.direction.name != "MAXIMIZE" or len(study.trials) != report["budget"]:
        raise ValueError("Optuna direction/budget differs from report")
    by_number = {trial.number: trial for trial in study.trials}
    for row in report["trials"]:
        trial = by_number[row["number"]]
        if (
            trial.state.name != row["state"]
            or trial.params != row["params"]
            or trial.value != row["value"]
            or trial.user_attrs.get("run_id") != row["run_id"]
            or trial.user_attrs.get("dev_predictions") != row["dev_predictions"]
        ):
            raise ValueError("Optuna trial differs from saved validation table")
        run = client.get_run(row["run_id"])
        require_local_artifact_uri(run.info.artifact_uri, artifact_root)
        if row["state"] == "COMPLETE" and run.info.status != "FINISHED":
            raise ValueError("complete trial must have a finished MLflow run")
        expected_tags = {
            "dataset_sha256": report["dataset_sha256"],
            "split_sha256": report["split_sha256"],
            "trial_number": str(row["number"]),
            "trial_state": row["state"],
            "objective": "dev_macro_f1",
            "direction": "maximize",
            "seed": str(report["seed"]),
        }
        if any(run.data.tags.get(key) != value for key, value in expected_tags.items()):
            raise ValueError("MLflow provenance tags differ")
        if any(run.data.params.get(key) != str(value) for key, value in row["params"].items()):
            raise ValueError("MLflow trial params differ")
        if row["state"] == "COMPLETE" and not math.isclose(
            run.data.metrics.get("dev_macro_f1", float("nan")), row["value"], abs_tol=1e-12
        ):
            raise ValueError("MLflow metric differs from predictions")
        run_dir = Path(url2pathname(urlsplit(run.info.artifact_uri).path))
        if read_json(run_dir / "trial.json") != row:
            raise ValueError("MLflow trial artifact differs from report")
    if study.best_trial.number != selected:
        raise ValueError("Optuna selected trial differs from saved selection")
    logged = client.get_logged_model(report["model_id"])
    if logged.source_run_id != report["selected_run_id"]:
        raise ValueError("logged model belongs to a different trial run")
    model_dir = local_model_directory(client, report["model_id"], artifact_root)
    if report.get("model_sha256") != model_digest(model_dir):
        raise ValueError("saved model flavor digest differs")
    # Load a verified file URI directly; no global tracker or remote model resolution.
    model = mlflow.sklearn.load_model(model_dir.as_uri())
    selected_row = next(row for row in report["trials"] if row["number"] == selected)
    verify_train_fit(model, dataset, selected_row["params"], seed=report["seed"])
    for split in ("dev", "holdout"):
        predictions = list(model.predict([row["text"] for row in dataset[split]]))
        if predictions != report[f"{split}_predictions"]:
            raise ValueError(f"reloaded model differs from saved {split} predictions")
    return {"mechanical_status": "VERIFIED", "learner_mastery": "REQUIRES_REVIEW"}


def verify_train_fit(
    model: Any, dataset: dict[str, Any], params: dict[str, Any], *, seed: int
) -> None:
    """Re-fit the declared sklearn pipeline on train; reject leaked fitted state."""
    import numpy as np
    from sklearn.base import clone
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    if (
        not isinstance(model, Pipeline)
        or list(model.named_steps) != ["tfidf", "classifier"]
        or not isinstance(model.named_steps["tfidf"], TfidfVectorizer)
        or not isinstance(model.named_steps["classifier"], LogisticRegression)
    ):
        raise ValueError("declared tfidf/classifier sklearn pipeline required")
    vectorizer, classifier = model.named_steps["tfidf"], model.named_steps["classifier"]
    if (
        params.get("C") != classifier.C
        or classifier.random_state != seed
        or vectorizer.ngram_range != (1, params.get("word_ngram"))
    ):
        raise ValueError("selected model hyperparameters differ from trial/seed")
    replay = clone(model)
    train = dataset["train"]
    replay.fit([row["text"] for row in train], [row["label"] for row in train])
    fresh_vectorizer, fresh_classifier = (
        replay.named_steps["tfidf"],
        replay.named_steps["classifier"],
    )
    if vectorizer.vocabulary_ != fresh_vectorizer.vocabulary_:
        raise ValueError("selected vectorizer differs from train-only fit")
    for actual, expected in (
        (vectorizer.idf_, fresh_vectorizer.idf_),
        (classifier.coef_, fresh_classifier.coef_),
        (classifier.intercept_, fresh_classifier.intercept_),
    ):
        if actual.shape != expected.shape or not np.allclose(
            actual, expected, rtol=1e-7, atol=1e-9
        ):
            raise ValueError("selected learned parameters differ from train-only fit")
    if list(classifier.classes_) != list(fresh_classifier.classes_):
        raise ValueError("selected classes differ from train-only fit")
