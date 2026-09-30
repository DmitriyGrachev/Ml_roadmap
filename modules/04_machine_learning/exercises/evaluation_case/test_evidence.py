"""Tiny arithmetic units, not a support-study submission."""

import importlib
import json
from pathlib import Path
from typing import Any

import pytest


def test_missing_evidence_is_rejected(tmp_path: Path) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    with pytest.raises(ValueError, match="invalid JSON"):
        module.validate_evidence(tmp_path)


def test_counts_come_from_labels_and_predictions() -> None:
    module = importlib.import_module(__package__ + ".evidence")
    assert module.summarize([0, 1, 1], [1, 1, 0]) == {
        "count": 3,
        "correct": 1,
        "tp": 1,
        "tn": 0,
        "fp": 1,
        "fn": 1,
        "accuracy": 1 / 3,
    }


@pytest.mark.parametrize("predictions", [[0], [0, 2], [True, 1]])
def test_invalid_prediction_domain(predictions: list[int]) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    with pytest.raises(ValueError, match=r"prediction count|binary integers"):
        module.summarize([0, 1], predictions)


def test_manifest_from_other_exercise_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "manifest.json").write_text(json.dumps({"exercise_id": "other"}))
    module = importlib.import_module(__package__ + ".evidence")
    with pytest.raises(ValueError, match="expected JSON object"):
        module.validate_evidence(tmp_path)


@pytest.mark.parametrize("change", [None, "run", "dataset", "split", "id", "metric", "bool"])
def test_saved_predictions_are_bound_and_recounted(change: str | None) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    identity = {"run_id": "toy", "dataset_sha256": "a" * 64, "split_sha256": "b" * 64}
    output: dict[str, Any] = {
        **identity,
        "predictions": [{"id": "fruit", "prediction": 1}],
        "accounting": {
            "count": 1,
            "correct": 0,
            "accuracy": 0.0,
            "tp": 0,
            "tn": 0,
            "fp": 1,
            "fn": 0,
        },
    }
    if change in ("run", "dataset", "split"):
        key = {"run": "run_id", "dataset": "dataset_sha256", "split": "split_sha256"}[change]
        output[key] = "foreign"
    elif change == "id":
        output["predictions"][0]["id"] = "vegetable"
    elif change == "metric":
        output["accounting"]["accuracy"] = 1.0
    elif change == "bool":
        output["accounting"]["count"] = True
    rows = [{"id": "fruit", "label": 0}]
    if change is None:
        module.validate_outputs(rows, ["fruit"], output, identity)
    else:
        with pytest.raises(ValueError, match=r"differs|IDs differ|numeric value"):
            module.validate_outputs(rows, ["fruit"], output, identity)


@pytest.mark.parametrize(
    ("train", "test"), [(["a"], ["a"]), (["a"], ["c"]), (["a"], ["b", "b"]), ([], ["a", "b"])]
)
def test_partition_rejects_overlap_foreign_duplicate_empty(
    train: list[str], test: list[str]
) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    with pytest.raises(ValueError, match=r"overlaps|cover input IDs|duplicate IDs|nonempty ID"):
        module.validate_split({"train_ids": train, "test_ids": test}, ["a", "b"])


def test_partition_preserves_explicit_order() -> None:
    module = importlib.import_module(__package__ + ".evidence")
    assert module.validate_split({"train_ids": ["b"], "test_ids": ["a"]}, ["a", "b"]) == (
        ["b"],
        ["a"],
    )
