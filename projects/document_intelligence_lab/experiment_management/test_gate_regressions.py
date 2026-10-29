"""Adversarial completion-gate probes; sentinels are never experiment evidence."""

from pathlib import Path
from typing import Any

import pytest

from ..artifacts import json_bytes
from . import starter, test_starter


def saved_sentinel(root: Path, *, identity: str = "original") -> Path:
    """Only exercise gate control flow; the real artifact validator is not under test."""
    root.mkdir()
    (root / "dataset.json").write_bytes(json_bytes({"train": [], "dev": [], "holdout": []}))
    (root / "experiment.json").write_bytes(
        json_bytes(
            {
                "budget": 2,
                "seed": 23,
                "dataset_sha256": "same-dataset",
                "trials": [{"run_id": f"{identity}-run-0"}, {"run_id": f"{identity}-run-1"}],
                "selected_run_id": f"{identity}-run-0",
                "model_id": f"{identity}-model",
            }
        )
    )
    (root / "study.sqlite").touch()
    (root / "runs.sqlite").touch()
    return root


def stub_artifact_check(monkeypatch: pytest.MonkeyPatch, original: Path) -> None:
    monkeypatch.setattr(test_starter, "required_evidence", lambda: original)
    monkeypatch.setattr(
        test_starter,
        "validate_experiment",
        lambda *args, **kwargs: {"mechanical_status": "VERIFIED"},
    )


def test_completion_rejects_returning_original_budget_two_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = saved_sentinel(tmp_path / "original")
    stub_artifact_check(monkeypatch, original)
    monkeypatch.setattr(starter, "run_search", lambda *args, **kwargs: original)
    with pytest.raises(AssertionError, match="requested fresh output"):
        test_starter.test_required_learner_artifacts_and_fresh_two_trial_rerun(tmp_path)


@pytest.mark.parametrize(
    "bad",
    ["same-identities", "same-model", "same-study", "same-runs", "missing-output", "overwrite"],
)
def test_completion_rejects_reused_identity_store_or_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    original = saved_sentinel(tmp_path / "original")
    stub_artifact_check(monkeypatch, original)

    def run(dataset: Any, output: Path, **kwargs: Any) -> Path:
        if output.exists():
            if bad == "overwrite":
                return output
            raise FileExistsError(output)
        if bad == "missing-output":
            return output
        saved_sentinel(output, identity="original" if bad == "same-identities" else "replay")
        if bad == "same-model":
            from ..artifacts import read_json

            report = read_json(output / "experiment.json")
            report["model_id"] = "original-model"
            (output / "experiment.json").write_bytes(json_bytes(report))
        if bad in {"same-study", "same-runs"}:
            name = "study.sqlite" if bad == "same-study" else "runs.sqlite"
            (output / name).unlink()
            (output / name).symlink_to(original / name)
        return output

    monkeypatch.setattr(starter, "run_search", run)
    message = {
        "same-identities": "identities",
        "same-study": "store",
        "same-runs": "store",
        "same-model": "model identities",
        "missing-output": "create requested fresh output",
        "overwrite": "DID NOT RAISE",
    }[bad]
    with pytest.raises((AssertionError, pytest.fail.Exception), match=message):
        test_starter.test_required_learner_artifacts_and_fresh_two_trial_rerun(tmp_path)


def test_fresh_distinct_rerun_control_flow_and_existing_output_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = saved_sentinel(tmp_path / "original")
    stub_artifact_check(monkeypatch, original)
    requests: list[Path] = []

    def run(dataset: Any, output: Path, **kwargs: Any) -> Path:
        requests.append(output)
        if output.exists():
            raise FileExistsError(output)
        return saved_sentinel(output, identity="replay")

    monkeypatch.setattr(starter, "run_search", run)
    test_starter.test_required_learner_artifacts_and_fresh_two_trial_rerun(tmp_path)
    assert requests == [tmp_path / "learner-rerun", tmp_path / "learner-rerun"]


class ProbeTrial:
    """Deterministic control-flow stand-in, not actual Optuna execution evidence."""

    def __init__(self) -> None:
        self.params: dict[str, Any] = {}
        self.user_attrs: dict[str, Any] = {}
        self.state = type("Complete", (), {"name": "COMPLETE"})()
        self.value: float | None = None

    def suggest_float(self, name: str, low: float, high: float, **kwargs: Any) -> float:
        self.params[name] = low
        return low

    def suggest_int(self, name: str, low: int, high: int, **kwargs: Any) -> int:
        self.params[name] = low
        return low

    def set_user_attr(self, name: str, value: Any) -> None:
        self.user_attrs[name] = value


class ProbeStudy:
    def __init__(self) -> None:
        self.trials: list[ProbeTrial] = []

    def optimize(self, objective: Any, *, n_trials: int, n_jobs: int) -> None:
        for _ in range(n_trials):
            trial = ProbeTrial()
            trial.value = objective(trial)
            self.trials.append(trial)


class ProbeOptuna:
    samplers = type("Samplers", (), {"RandomSampler": staticmethod(lambda **kwargs: None)})

    @staticmethod
    def create_study(**kwargs: Any) -> ProbeStudy:
        return ProbeStudy()


@pytest.mark.parametrize("bad", ["copy-labels", "constant", "dummy-parameter"])
def test_objective_gate_rejects_no_sklearn_fit_predict(
    monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    from . import runtime
    from .protocol import macro_f1

    def build(train: Any, dev: Any, **kwargs: Any) -> Any:
        def objective(trial: ProbeTrial) -> float:
            if bad == "dummy-parameter":
                trial.suggest_int("dummy", 1, 2)
            else:
                trial.suggest_float("C", 0.1, 2.0)
                trial.suggest_int("word_ngram", 1, 2)
            predictions = (
                [row["label"] for row in dev] if bad != "constant" else ["support"] * len(dev)
            )
            trial.set_user_attr("dev_predictions", predictions)
            return (
                1 / 3 if bad == "constant" else macro_f1([row["label"] for row in dev], predictions)
            )

        return objective

    monkeypatch.setattr(starter, "build_objective", build)
    monkeypatch.setattr(runtime, "libraries", lambda: (None, ProbeOptuna))
    with pytest.raises(AssertionError, match=r"fit|parameters"):
        test_starter.test_learner_objective_receives_train_dev_and_returns_verified_metric(
            monkeypatch
        )


@pytest.mark.parametrize(
    ("fault", "message"),
    [
        ("none", None),
        ("train-order", "ordered train"),
        ("dev-order", "ordered dev"),
        ("copied-labels", "saved predictions"),
        ("ignored-params", "declared C"),
    ],
)
def test_objective_observer_checks_real_tiny_pipeline_inputs_params_and_outputs(
    monkeypatch: pytest.MonkeyPatch, fault: str, message: str | None
) -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    from . import runtime
    from .protocol import macro_f1

    def build(train: Any, dev: Any, *, seed: int) -> Any:
        def objective(trial: ProbeTrial) -> float:
            regularization = trial.suggest_float("C", 0.1, 2.0)
            ngram = trial.suggest_int("word_ngram", 1, 2)
            model = Pipeline(
                [
                    ("tfidf", TfidfVectorizer(ngram_range=(1, ngram))),
                    (
                        "classifier",
                        LogisticRegression(
                            C=2.0 if fault == "ignored-params" else regularization,
                            random_state=seed,
                            max_iter=100,
                        ),
                    ),
                ]
            )
            fit_rows = train[::-1] if fault == "train-order" else train
            predict_rows = dev[::-1] if fault == "dev-order" else dev
            model.fit([row["text"] for row in fit_rows], [row["label"] for row in fit_rows])
            predictions = list(model.predict([row["text"] for row in predict_rows]))
            if fault == "copied-labels":
                predictions = [row["label"] for row in dev]
            trial.set_user_attr("dev_predictions", predictions)
            return macro_f1([row["label"] for row in dev], predictions)

        return objective

    monkeypatch.setattr(starter, "build_objective", build)
    monkeypatch.setattr(runtime, "libraries", lambda: (None, ProbeOptuna))
    if message is None:
        test_starter.test_learner_objective_receives_train_dev_and_returns_verified_metric(
            monkeypatch
        )
    else:
        with pytest.raises(AssertionError, match=message):
            test_starter.test_learner_objective_receives_train_dev_and_returns_verified_metric(
                monkeypatch
            )
