"""Fixed teacher traces, not extra requirements for learner check."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

torch = pytest.importorskip("torch", reason="Optional training environment")
pytest.importorskip("transformers", reason="Optional training environment")


def demo() -> Any:
    return importlib.import_module("labs.02_huggingface_models.walkthrough")


def test_fixed_attention_matches_hand_arithmetic_and_mask() -> None:
    result = demo().fixed_attention()
    assert result["shapes"] == {
        "q": [1, 1, 1, 2],
        "k": [1, 1, 3, 2],
        "v": [1, 1, 3, 2],
        "allowed": [1, 1, 1, 3],
        "output": [1, 1, 1, 2],
    }
    assert result["scaled_scores"] == pytest.approx([1.0, 0.0, 6.36396103068])
    assert result["masked_scores"] == [1.0, 0.0, "-inf"]
    assert result["weights"] == pytest.approx([0.73105857863, 0.26894142137, 0.0])
    assert result["output"] == pytest.approx([1.46211715726, 1.07576568548])
    assert result["manual_max_difference"] < 1e-12
    assert result["masked_value_change_max_difference"] < 1e-12
    assert result["allowed_value_change_max_difference"] == pytest.approx(0.73105857863)
    assert result["grad_v"][2] == [0.0, 0.0]
    assert result["grad_k"][2] == [0.0, 0.0]
    assert result["grad_v"][0] == pytest.approx([0.73105857863, 0.73105857863])
    assert all(abs(value) < 100 for row in result["grad_k"] for value in row)


def test_local_tokenizer_encoder_pooler_and_mask_trace() -> None:
    result = demo().text_trace()
    assert result["input_ids"] == [[2, 5, 3, 0, 0], [2, 12, 6, 8, 3]]
    assert result["attention_mask"] == [[1, 1, 1, 0, 0], [1, 1, 1, 1, 1]]
    assert result["token_type_ids"] == [[0] * 5, [0] * 5]
    assert result["tokens"][0] == ["[CLS]", "red", "[SEP]", "[PAD]", "[PAD]"]
    assert result["input_dtype"] == "torch.int64"
    assert result["shapes"] == {
        "word_lookup": [2, 5, 16],
        "embeddings": [2, 5, 16],
        "hidden": [2, 5, 16],
        "pooler": [2, 16],
        "logits": [2, 2],
    }
    assert result["pooler_formula_max_difference"] < 1e-7
    assert result["head_max_difference"] < 1e-7
    assert result["masked_id_change_max_difference"] < 1e-7
    assert result["unmasked_id_change_max_difference"] > 1e-8
    assert result["truncated_ids"] == [2, 12, 6, 3]
    assert result["unknown_ids"] == [2, 1, 3]
    assert result["single_vs_batch_max_difference"] < 1e-6
    assert result["pretrained_quality"] == "NOT_RUN"


def test_teacher_export_is_reproducible_local_and_reloadable(tmp_path: Path) -> None:
    before = torch.get_rng_state().clone()
    first = demo().run_walkthrough(tmp_path / "first")
    assert torch.equal(before, torch.get_rng_state())
    second = demo().run_walkthrough(tmp_path / "second")
    assert first == second
    assert first["text"]["initialization_seed"] == 17
    assert first["smoke"]["reload_max_abs_difference"] < 1e-7
    assert first["quality_claim"] is False
    assert (tmp_path / "first/local-model/model.safetensors").is_file()
    assert json.loads((tmp_path / "first/trace.json").read_text()) == first


def test_teacher_output_refuses_existing_directory(tmp_path: Path) -> None:
    with pytest.raises(FileExistsError):
        demo().run_walkthrough(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_attention_plot_opt_in(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib", reason="Optional visualization environment")
    result = demo().run_walkthrough(tmp_path / "plot", plots=True)
    assert result["plots"] == ["attention.png"]
    assert (tmp_path / "plot/attention.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
