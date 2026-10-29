from importlib import import_module
from typing import Any

import pytest

h = import_module("labs.02_huggingface_models.token_classification.training_evidence")


@pytest.mark.parametrize("mode", ["forward_only", "backward_without_update"])
def test_forward_only_counterfeit_is_rejected(monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    torch = pytest.importorskip("torch", reason="uv sync --group trainer")
    t = pytest.importorskip("transformers", reason="uv sync --group trainer")
    torch.set_num_threads(1)
    model = t.AutoModelForTokenClassification.from_config(
        t.BertConfig(
            vocab_size=8,
            hidden_size=8,
            num_hidden_layers=1,
            num_attention_heads=2,
            intermediate_size=12,
        )
    )
    evidence = h.observe_optimization(model, monkeypatch)
    # Deliberately wrong implementation performs a genuine forward/loss, then stops.
    model.train()
    output = model(input_ids=torch.tensor([[2, 5, 3]]), labels=torch.tensor([[-100, 1, -100]]))
    if mode == "backward_without_update":
        output.loss.backward()
    with pytest.raises(AssertionError, match=r"backward|parameters"):
        h.require_optimization(evidence, model)


def test_report_requires_disjoint_splits_and_raw_validation_history() -> None:
    p = import_module("labs.02_huggingface_models.token_classification.protocol")
    good: dict[str, Any] = {
        "split_ids": {"train": ["a"], "validation": ["b"], "test": ["c"]},
        "predictions": [["O"]],
        "references": [["O"]],
        "history": [{"step": 1, "eval_loss": 0.2, "eval_f1": 0.0}],
    }
    p.validate_report_structure(good)
    for key in ["split_ids", "history"]:
        bad = dict(good)
        bad.pop(key)
        with pytest.raises(ValueError, match=key):
            p.validate_report_structure(bad)
    bad = dict(good, split_ids={"train": ["a"], "validation": ["a"], "test": ["c"]})
    with pytest.raises(ValueError, match="overlap"):
        p.validate_report_structure(bad)
