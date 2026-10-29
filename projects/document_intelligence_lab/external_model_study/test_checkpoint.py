"""Optional local random-weight test of real save/load APIs; pretrained quality NOT_RUN."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def test_author_checkpoint_smoke_reloads_local_safetensors(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    factory = importlib.import_module("labs.02_huggingface_models.example")
    model, tokenizer = factory.make_local_components()
    module = importlib.import_module(
        "projects.document_intelligence_lab.external_model_study.pretrained_smoke"
    )
    result = module.checkpoint_smoke(
        model.bert, tokenizer, ["red", "large blue square"], tmp_path / "checkpoint"
    )
    assert result["embedding_shape"] == [2, 16]
    assert result["padding_tokens"] > 0
    assert result["finite"] is True
    assert result["reload_max_abs_difference"] == 0.0
    assert result["quality_evaluation"] == "NOT_RUN"
    assert (tmp_path / "checkpoint" / "model.safetensors").is_file()
