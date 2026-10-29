"""Local retained-artifact regressions; no optimization or author example run."""

from importlib import import_module
from pathlib import Path

import pytest

p = import_module("labs.02_huggingface_models.trainer_workflow.protocol")


def test_declared_manual_budget_is_separate_from_smoke_budget() -> None:
    assert p.RunConfig(max_steps=100).max_steps == 100
    for value in (101, True, 0):
        with pytest.raises(ValueError):  # noqa: PT011 - diagnostic wording is not material
            p.RunConfig(max_steps=value)


@pytest.mark.parametrize("kind", ["sequence", "token"])
def test_saved_artifact_rejects_deleted_or_changed_weights_and_tokenizer(
    tmp_path: Path, kind: str
) -> None:
    t = pytest.importorskip("transformers", reason="uv sync --group trainer")
    torch = pytest.importorskip("torch", reason="uv sync --group trainer")
    torch.set_num_threads(1)
    config = t.BertConfig(
        vocab_size=8,
        hidden_size=8,
        num_hidden_layers=1,
        num_attention_heads=2,
        intermediate_size=12,
    )
    constructor = (
        t.AutoModelForSequenceClassification
        if kind == "sequence"
        else t.AutoModelForTokenClassification
    )
    model = constructor.from_config(config)
    tokenizer = t.BertTokenizerFast(
        vocab={
            word: i
            for i, word in enumerate(
                ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "ad", "##a", "."]
            )
        }
    )
    artifact = tmp_path / kind
    model.save_pretrained(artifact, safe_serialization=True)
    tokenizer.save_pretrained(artifact)
    identity, token_identity = p.model_fingerprint(model), p.tokenizer_fingerprint(tokenizer)
    p.validate_saved_artifact(artifact, kind, identity, token_identity)
    with torch.no_grad():
        next(model.parameters()).add_(1.0)
    model.save_pretrained(artifact, safe_serialization=True)
    with pytest.raises(ValueError, match="model fingerprint"):
        p.validate_saved_artifact(artifact, kind, identity, token_identity)
    identity = p.model_fingerprint(model)
    tokenizer.add_tokens(["changed"])
    tokenizer.save_pretrained(artifact)
    with pytest.raises(ValueError, match="tokenizer fingerprint"):
        p.validate_saved_artifact(artifact, kind, identity, token_identity)
    (artifact / "model.safetensors").unlink()
    with pytest.raises(ValueError, match="checkpoint"):
        p.validate_saved_artifact(artifact, kind, identity, token_identity)
