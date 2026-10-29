"""Author-only four-trial invoice/ticket mechanism example, never learner credit.

This deliberately concrete fixture is not a configurable implementation of the learner
boundaries. It does not install packages, start a tracking UI, or access the network.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..artifacts import file_sha256, json_bytes
from ..tracking_intro.demo import require_local_artifact_uri
from .protocol import digest, macro_f1, objective_inputs, select_best, split_digest
from .runtime import libraries, local_model_directory, local_paths, model_digest


def author_dataset() -> dict[str, list[dict[str, str]]]:
    """Small distinct synthetic domain; human transfer must use different documents."""
    texts = {
        "train": [
            ("invoice total amount payable", "invoice"),
            ("invoice balance payment due", "invoice"),
            ("invoice tax amount billed", "invoice"),
            ("invoice payment bank account", "invoice"),
            ("ticket flight boarding gate", "ticket"),
            ("ticket departure seat number", "ticket"),
            ("ticket flight passenger boarding", "ticket"),
            ("ticket airline departure terminal", "ticket"),
        ],
        "dev": [
            ("invoice payable balance", "invoice"),
            ("invoice tax payment", "invoice"),
            ("ticket passenger seat", "ticket"),
            ("ticket boarding terminal", "ticket"),
        ],
        "holdout": [
            ("invoice bank tax", "invoice"),
            ("invoice billed balance", "invoice"),
            ("ticket airline gate", "ticket"),
            ("ticket flight seat", "ticket"),
        ],
    }
    return {
        split: [
            {"id": f"{split}-{i}", "family": f"{split}-source-{i}", "text": text, "label": label}
            for i, (text, label) in enumerate(rows)
        ]
        for split, rows in texts.items()
    }


def run_demo(output: Path) -> Path:
    if output.exists():
        raise FileExistsError(f"experiment output already exists: {output}")
    mlflow, optuna = libraries()  # Missing runtime cannot produce a successful artifact.
    import numpy as np
    import sklearn
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    dataset = author_dataset()
    inputs = objective_inputs(dataset)
    train, dev = inputs["train"], inputs["dev"]
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    _, artifact_root, tracking_uri, artifact_uri = local_paths(output)
    artifact_root.mkdir()
    client = mlflow.MlflowClient(tracking_uri=tracking_uri, registry_uri=tracking_uri)
    experiment_id = client.create_experiment(
        "author-invoice-ticket", artifact_location=artifact_uri
    )
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_registry_uri(tracking_uri)
    study_name, seed = "author-invoice-ticket", 23
    study = optuna.create_study(
        study_name=study_name,
        direction="maximize",
        sampler=optuna.samplers.RandomSampler(seed=seed),
        storage="sqlite:///" + (output / "study.sqlite").as_posix(),
    )
    rows: list[dict[str, Any]] = []
    models: dict[int, Any] = {}

    def invoice_objective(trial: Any) -> float:
        # No holdout closure read: fit/predict receive only the validated train/dev copies.
        regularization = trial.suggest_float("C", 0.1, 2.0, log=True)
        ngram = trial.suggest_int("word_ngram", 1, 2)
        model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, ngram))),
                (
                    "classifier",
                    LogisticRegression(C=regularization, random_state=seed, max_iter=100),
                ),
            ]
        )
        model.fit([row["text"] for row in train], [row["label"] for row in train])
        predictions = list(model.predict([row["text"] for row in dev]))
        value = macro_f1([row["label"] for row in dev], predictions)
        with mlflow.start_run(experiment_id=experiment_id, run_name=f"trial-{trial.number}") as run:
            require_local_artifact_uri(run.info.artifact_uri, artifact_root)
            row = {
                "number": trial.number,
                "state": "COMPLETE",
                "value": value,
                "params": dict(trial.params),
                "run_id": run.info.run_id,
                "dev_predictions": predictions,
                "dev_ids": [row["id"] for row in dev],
                "fit_ids": [row["id"] for row in train],
            }
            trial.set_user_attr("run_id", run.info.run_id)
            trial.set_user_attr("dev_predictions", predictions)
            mlflow.log_params(trial.params)
            mlflow.log_metric("dev_macro_f1", value)
            mlflow.set_tags(
                {
                    "dataset_sha256": digest(dataset),
                    "split_sha256": split_digest(dataset),
                    "trial_number": str(trial.number),
                    "trial_state": "COMPLETE",
                    "objective": "dev_macro_f1",
                    "direction": "maximize",
                    "seed": str(seed),
                }
            )
            mlflow.log_dict(row, "trial.json")
        rows.append(row)
        models[trial.number] = model
        return value

    study.optimize(invoice_objective, n_trials=4, n_jobs=1)
    selected = select_best(rows, "maximize")
    best = next(row for row in rows if row["number"] == selected)
    model = models[selected]
    # Final holdout is first touched only after selection has been frozen.
    holdout_predictions = list(model.predict([row["text"] for row in dataset["holdout"]]))
    with mlflow.start_run(run_id=best["run_id"]):
        info = mlflow.sklearn.log_model(
            sk_model=model,
            name="selected_pipeline",
            serialization_format="pickle",
            signature=mlflow.models.infer_signature(
                np.array([row["text"] for row in dev]), np.array(best["dev_predictions"])
            ),
            input_example=np.array([dev[0]["text"]]),
            pip_requirements=[f"scikit-learn=={sklearn.__version__}", f"numpy=={np.__version__}"],
        )
    model_dir = local_model_directory(client, info.model_id, artifact_root)
    reloaded = mlflow.sklearn.load_model(model_dir.as_uri())
    if list(reloaded.predict([row["text"] for row in dev])) != best["dev_predictions"]:
        raise ValueError("author saved model dev replay mismatch")
    report = {
        "schema_version": 1,
        "exercise_id": "ml-experiment-management",
        "evidence_kind": "AUTHOR_SYNTHETIC_EXPERIMENT_SMOKE_ONLY",
        "code_sha256": file_sha256(Path(__file__)),
        "dataset_sha256": digest(dataset),
        "split_sha256": split_digest(dataset),
        "objective": "dev_macro_f1",
        "direction": "maximize",
        "seed": seed,
        "budget": 4,
        "study_name": study_name,
        "selected_trial": selected,
        "trials": rows,
        "selected_run_id": best["run_id"],
        "model_id": info.model_id,
        "model_uri": info.model_uri,
        "model_sha256": model_digest(model_dir),
        "dev_predictions": best["dev_predictions"],
        "holdout_predictions": holdout_predictions,
        "holdout_macro_f1": macro_f1(
            [row["label"] for row in dataset["holdout"]], holdout_predictions
        ),
        "versions": {
            "mlflow": mlflow.__version__,
            "optuna": optuna.__version__,
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
        },
        "quality_defense": "REQUIRES_REVIEW",
    }
    (output / "dataset.json").write_bytes(json_bytes(dataset))
    (output / "experiment.json").write_bytes(json_bytes(report))
    return output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(run_demo(args.output))
    except RuntimeError as exc:
        parser.exit(status=2, message=f"{exc}\n")


if __name__ == "__main__":
    main()
