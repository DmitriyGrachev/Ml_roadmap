"""Pure adversarial selection, objective boundary and prediction checks."""

import copy

import pytest

from .protocol import macro_f1, objective_inputs, select_best, validate_table


def trial(number: int, value: float, state: str = "COMPLETE") -> dict[str, object]:
    return {"number": number, "state": state, "value": value}


def dataset() -> dict[str, list[dict[str, str]]]:
    return {
        split: [
            {"id": f"{split}-{i}", "family": f"{split}-{i}", "text": text, "label": label}
            for i, (text, label) in enumerate(rows)
        ]
        for split, rows in {
            "train": [("invoice total", "bill"), ("travel ticket", "ticket")],
            "dev": [("invoice balance", "bill"), ("travel pass", "ticket")],
            "holdout": [("final amount", "bill"), ("boarding gate", "ticket")],
        }.items()
    }


def test_direction_failure_pruning_and_deterministic_ties() -> None:
    rows = [trial(0, 0.8), trial(1, 0.2), trial(2, 9, "FAIL"), trial(3, -9, "PRUNED")]
    assert select_best(rows, "maximize") == 0
    assert select_best(rows, "minimize") == 1
    assert select_best([trial(4, 0.5), trial(2, 0.5)], "maximize") == 2
    with pytest.raises(ValueError, match="complete"):
        select_best([trial(0, 1, "FAIL")], "maximize")
    with pytest.raises(ValueError, match="direction"):
        select_best(rows, "max")


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_nonfinite_complete_trial_rejected(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        select_best([trial(0, value)], "maximize")


@pytest.mark.parametrize("overlap", ["id", "family", "text"])
def test_holdout_contamination_rejected(overlap: str) -> None:
    source = dataset()
    source["holdout"][0][overlap] = source["train"][0][overlap]
    with pytest.raises(ValueError, match="overlap"):
        objective_inputs(source)


def test_objective_has_only_copied_train_and_dev() -> None:
    source = dataset()
    before = copy.deepcopy(source)
    inputs = objective_inputs(source)
    assert set(inputs) == {"train", "dev"}
    inputs["train"][0]["text"] = "mutated"
    assert source == before


def test_macro_f1_and_saved_trial_values_come_from_predictions() -> None:
    assert macro_f1(["a", "a", "b", "b"], ["a", "a", "a", "b"]) == pytest.approx(11 / 15)
    rows = [
        {"number": 0, "state": "COMPLETE", "value": 1.0, "dev_predictions": ["a", "b"]},
        {"number": 1, "state": "FAIL", "value": 10.0, "dev_predictions": []},
    ]
    assert validate_table(rows, ["a", "b"], selected=0, budget=2) == 0
    rows[0]["value"] = 0.25
    with pytest.raises(ValueError, match="predictions"):
        validate_table(rows, ["a", "b"], selected=0, budget=2)


def test_wrong_selected_trial_and_unbounded_table_rejected() -> None:
    rows = [
        {"number": 0, "state": "COMPLETE", "value": 1.0, "dev_predictions": ["a", "b"]},
        {"number": 1, "state": "COMPLETE", "value": 0.0, "dev_predictions": ["b", "a"]},
    ]
    with pytest.raises(ValueError, match="selected"):
        validate_table(rows, ["a", "b"], selected=1, budget=2)
    with pytest.raises(ValueError, match="budget"):
        validate_table(rows, ["a", "b"], selected=0, budget=1)
