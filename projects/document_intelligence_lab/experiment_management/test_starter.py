"""Completion targets: learner selection, objective, saved evidence and fresh rerun only."""

import math
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from roadmap_tools import exercise_call

from ..artifacts import read_json
from . import starter
from .evidence import required_evidence, validate_experiment
from .protocol import macro_f1


def observed_objective(
    objective: Callable[[Any], float],
    train: list[dict[str, str]],
    dev: list[dict[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[Any], float]:
    """Test-only observer: call the original sklearn methods and audit each trial."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    fit_calls: list[dict[str, Any]] = []
    predict_calls: list[dict[str, Any]] = []
    real_fit, real_predict = Pipeline.fit, Pipeline.predict
    train_texts, train_labels = [r["text"] for r in train], [r["label"] for r in train]
    dev_texts, dev_labels = [r["text"] for r in dev], [r["label"] for r in dev]

    def fit(model: Any, texts: Any, labels: Any = None, **kwargs: Any) -> Any:
        inputs, targets = list(texts), list(labels) if labels is not None else None
        result = real_fit(model, texts, labels, **kwargs)
        fit_calls.append({"model": model, "texts": inputs, "labels": targets})
        return result

    def predict(model: Any, texts: Any, **kwargs: Any) -> Any:
        inputs = list(texts)
        result = real_predict(model, texts, **kwargs)
        predict_calls.append({"model": model, "texts": inputs, "predictions": list(result)})
        return result

    monkeypatch.setattr(Pipeline, "fit", fit)
    monkeypatch.setattr(Pipeline, "predict", predict)

    def checked(trial: Any) -> float:
        first_fit, first_predict = len(fit_calls), len(predict_calls)
        value = objective(trial)
        assert set(trial.params) == {"C", "word_ngram"}, "declared search parameters required"
        fits, predictions = fit_calls[first_fit:], predict_calls[first_predict:]
        assert len(fits) == 1, "each trial must perform one actual sklearn Pipeline.fit"
        assert len(predictions) == 1, "each trial must perform one actual sklearn Pipeline.predict"
        fitted, predicted = fits[0], predictions[0]
        assert fitted["texts"] == train_texts, "fit must receive ordered train texts only"
        assert fitted["labels"] == train_labels, "fit must receive ordered train labels only"
        assert predicted["texts"] == dev_texts, "predict must receive ordered dev texts"
        model = fitted["model"]
        assert predicted["model"] is model, "predict must use the fitted trial pipeline"
        assert list(model.named_steps) == ["tfidf", "classifier"]
        vectorizer, classifier = model.named_steps["tfidf"], model.named_steps["classifier"]
        assert isinstance(vectorizer, TfidfVectorizer)
        assert isinstance(classifier, LogisticRegression)
        assert trial.params["C"] == classifier.C, "declared C must configure fitted pipeline"
        assert (1, trial.params["word_ngram"]) == vectorizer.ngram_range, (
            "declared word_ngram must configure fitted pipeline"
        )
        assert trial.user_attrs["dev_predictions"] == predicted["predictions"], (
            "saved predictions must match observed sklearn outputs"
        )
        assert math.isclose(value, macro_f1(dev_labels, predicted["predictions"]), abs_tol=1e-12)
        return value

    return checked


@pytest.mark.student_exercise
def test_learner_selection_excludes_failure_and_respects_direction() -> None:
    rows = [
        {"number": 0, "state": "COMPLETE", "value": 0.7},
        {"number": 1, "state": "COMPLETE", "value": 0.3},
        {"number": 2, "state": "FAIL", "value": 5.0},
        {"number": 3, "state": "PRUNED", "value": -5.0},
    ]
    assert exercise_call(starter.select_trial, rows, "maximize") == 0
    assert starter.select_trial(rows, "minimize") == 1
    assert starter.select_trial([rows[1], {**rows[1], "number": 4}], "maximize") == 1
    with pytest.raises(ValueError, match="complete"):
        starter.select_trial([rows[2]], "maximize")
    with pytest.raises(ValueError, match="finite"):
        starter.select_trial([{**rows[0], "value": float("nan")}], "maximize")


@pytest.mark.student_exercise
def test_learner_objective_receives_train_dev_and_returns_verified_metric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A separate tiny boundary probe, not the author domain and not saved learner evidence.
    train = [
        {"id": "train-a", "family": "a", "text": "support broken device", "label": "support"},
        {"id": "train-b", "family": "b", "text": "support repair device", "label": "support"},
        {"id": "train-c", "family": "c", "text": "sales purchase order", "label": "sales"},
        {"id": "train-d", "family": "d", "text": "sales new order", "label": "sales"},
    ]
    dev = [
        # Deliberate label noise makes copying targets distinguishable from real predictions.
        {"id": "dev-a", "family": "e", "text": "support device", "label": "sales"},
        {"id": "dev-b", "family": "f", "text": "sales order", "label": "support"},
    ]
    objective = exercise_call(starter.build_objective, train, dev, seed=23)
    from .runtime import libraries

    _, optuna = libraries()
    # Two trials maximum; this is a learner boundary test, not an author benchmark.
    study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.RandomSampler(seed=23)
    )
    study.optimize(observed_objective(objective, train, dev, monkeypatch), n_trials=2, n_jobs=1)
    for trial in study.trials:
        assert trial.state.name == "COMPLETE"
        assert trial.params, "objective must actually suggest pipeline hyperparameters"
        assert math.isclose(
            trial.value,
            macro_f1([r["label"] for r in dev], trial.user_attrs["dev_predictions"]),
            abs_tol=1e-12,
        )


@pytest.mark.student_exercise
def test_required_learner_artifacts_and_fresh_two_trial_rerun(tmp_path: Path) -> None:
    root = exercise_call(required_evidence)
    trusted = os.environ.get("ROADMAP_EXPERIMENT_TRUST_LOCAL") == "1"
    assert (
        validate_experiment(root, trusted_local_artifact=trusted)["mechanical_status"] == "VERIFIED"
    )
    dataset: dict[str, Any] = read_json(root / "dataset.json")
    original = read_json(root / "experiment.json")
    requested = tmp_path / "learner-rerun"
    assert not requested.exists(), "requested output must start fresh"
    replay = exercise_call(starter.run_search, dataset, requested, seed=original["seed"], budget=2)
    assert replay.resolve() == requested.resolve(), "run_search must return requested fresh output"
    assert requested.is_dir(), "run_search must create requested fresh output"
    for name in ("study.sqlite", "runs.sqlite"):
        assert (root / name).resolve() != (replay / name).resolve(), "rerun needs a distinct store"
    assert (
        validate_experiment(replay, trusted_local_artifact=trusted)["mechanical_status"]
        == "VERIFIED"
    )
    report = read_json(replay / "experiment.json")
    assert report["budget"] == 2
    assert report["seed"] == original["seed"]
    assert report["dataset_sha256"] == original["dataset_sha256"]
    assert not {row["run_id"] for row in report["trials"]} & {
        row["run_id"] for row in original["trials"]
    }, "rerun requires new trial run identities"
    assert report["model_id"] != original["model_id"], "rerun requires new model identities"
    assert report["selected_run_id"] != original["selected_run_id"], (
        "rerun requires new selected run identities"
    )
    with pytest.raises(FileExistsError):
        starter.run_search(dataset, requested, seed=original["seed"], budget=2)
