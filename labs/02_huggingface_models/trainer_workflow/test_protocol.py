from importlib import import_module

import pytest

p = import_module("labs.02_huggingface_models.trainer_workflow.protocol")


def test_split_and_label_contract() -> None:
    rows = {
        "train": [{"id": "a", "text": "one", "label": 0}],
        "validation": [{"id": "b", "text": "two", "label": 1}],
        "test": [{"id": "c", "text": "three", "label": 0}],
    }
    p.validate_splits(rows, {0: "A", 1: "B"})
    rows["test"][0]["id"] = "a"
    with pytest.raises(ValueError, match="overlap"):
        p.validate_splits(rows, {0: "A", 1: "B"})
    rows["test"][0]["id"] = "c"
    rows["test"][0]["label"] = 2
    with pytest.raises(ValueError, match="label"):
        p.validate_splits(rows, {0: "A", 1: "B"})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_steps": 101},
        {"max_steps": True},
        {"batch_size": 0},
        {"learning_rate": float("nan")},
        {"seed": -1},
    ],
)
def test_budget_rejects_invalid(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - learner diagnostic text is free
        p.RunConfig(**kwargs)


def test_config_mapping_must_match() -> None:
    with pytest.raises(ValueError, match="mapping"):
        p.validate_model_mapping({0: "A", 1: "B"}, {"A": 1, "B": 0}, {0: "A", 1: "B"})
