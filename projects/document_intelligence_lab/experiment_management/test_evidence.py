"""Base evidence rejects author credit, forged metrics and contaminated source."""

import copy
from pathlib import Path
from typing import Any

import pytest

from ..artifacts import json_bytes
from .evidence import required_evidence, validate_report
from .protocol import digest, split_digest
from .test_protocol import dataset


def report() -> dict[str, Any]:
    source = dataset()
    return {
        "schema_version": 1,
        "exercise_id": "ml-experiment-management",
        "evidence_kind": "STUDENT_EXPERIMENT_MANAGEMENT",
        "dataset_sha256": digest(source),
        "split_sha256": split_digest(source),
        "direction": "maximize",
        "objective": "dev_macro_f1",
        "seed": 23,
        "budget": 2,
        "selected_trial": 0,
        "trials": [
            {
                "number": number,
                "state": "COMPLETE",
                "value": value,
                "params": {"C": 0.1 + number},
                "run_id": f"run-{number}",
                "dev_predictions": predictions,
                "dev_ids": [row["id"] for row in source["dev"]],
                "fit_ids": [row["id"] for row in source["train"]],
            }
            for number, value, predictions in [
                (0, 1.0, ["bill", "ticket"]),
                (1, 0.0, ["ticket", "bill"]),
            ]
        ],
        "dev_predictions": ["bill", "ticket"],
        "holdout_predictions": ["bill", "ticket"],
        "holdout_macro_f1": 1.0,
        "selected_run_id": "run-0",
        "model_id": "m-test",
        "model_uri": "models:/m-test",
        "quality_defense": "REQUIRES_REVIEW",
    }


def test_missing_saved_evidence_is_unfinished(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROADMAP_EXPERIMENT_EVIDENCE", raising=False)
    with pytest.raises(NotImplementedError, match="learner"):
        required_evidence()


def test_complete_pure_report_still_needs_runtime_verification() -> None:
    assert validate_report(report(), dataset()) == 0


@pytest.mark.parametrize("change", ["author", "metric", "selection", "fit", "digest", "direction"])
def test_forged_or_contaminated_reports_are_rejected(change: str) -> None:
    saved = copy.deepcopy(report())
    if change == "author":
        saved["evidence_kind"] = "AUTHOR_SYNTHETIC_EXPERIMENT_SMOKE_ONLY"
    elif change == "metric":
        saved["holdout_macro_f1"] = 0.25
    elif change == "selection":
        saved["selected_trial"] = 1
    elif change == "fit":
        saved["trials"][0]["fit_ids"].append("holdout-0")
    elif change == "digest":
        saved["dataset_sha256"] = "0" * 64
    else:
        saved["direction"] = "minimize"
    message = {
        "author": "identity/evidence",
        "metric": "holdout metric",
        "selection": "selected",
        "fit": "fit IDs",
        "digest": "digest",
        "direction": "explicit",
    }[change]
    with pytest.raises(ValueError, match=message):
        validate_report(saved, dataset())


def test_author_saved_report_rejected_before_optional_import(tmp_path: Path) -> None:
    from .evidence import validate_experiment

    saved = report()
    saved["evidence_kind"] = "AUTHOR_SYNTHETIC_EXPERIMENT_SMOKE_ONLY"
    (tmp_path / "experiment.json").write_bytes(json_bytes(saved))
    (tmp_path / "dataset.json").write_bytes(json_bytes(dataset()))
    with pytest.raises(ValueError, match="identity/evidence"):
        validate_experiment(tmp_path, trusted_local_artifact=True)


def test_selected_model_must_reproduce_train_only_fit() -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    from .evidence import verify_train_fit

    source = dataset()
    params = {"C": 0.5, "word_ngram": 1}
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("classifier", LogisticRegression(C=0.5, random_state=23, max_iter=100)),
        ]
    )
    train = source["train"]
    model.fit([r["text"] for r in train], [r["label"] for r in train])
    verify_train_fit(model, source, params, seed=23)
    contaminated = train + source["holdout"]
    model.fit([r["text"] for r in contaminated], [r["label"] for r in contaminated])
    with pytest.raises(ValueError, match="train-only"):
        verify_train_fit(model, source, params, seed=23)
