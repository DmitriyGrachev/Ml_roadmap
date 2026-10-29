"""Explicit learner real-library contract; set ROADMAP_RUN_SFT=1. No author fallback."""

import os
from importlib import import_module
from pathlib import Path

import pytest

from roadmap_tools.exercise import exercise_call

pytestmark = pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_SFT") != "1",
    reason="Explicit --group sft and ROADMAP_RUN_SFT=1 required",
)


def test_learner_real_trainer_and_saved_adapter(tmp_path: Path) -> None:
    import torch
    from peft import PeftModel
    from safetensors.torch import load_file
    from transformers import AutoModelForCausalLM
    from trl.trainer.sft_config import SFTConfig
    from trl.trainer.sft_trainer import SFTTrainer

    starter = import_module("labs.04_llm_finetuning.sft_workflow.starter")
    fixture = import_module("labs.04_llm_finetuning.sft_workflow.author_fixture")
    torch.set_num_threads(1)
    torch.manual_seed(17)
    base, tokenizer = fixture.tiny_components()
    base.save_pretrained(tmp_path / "base", safe_serialization=True)
    # Probe each learner boundary before running any actual optimization.
    rows = [
        exercise_call(starter.encode_conversation, tokenizer, row, 8) for row in fixture.CORPUS[:2]
    ]
    trainer = exercise_call(starter.build_trainer, base, tokenizer, rows, tmp_path / "run", 2)
    assert isinstance(trainer, SFTTrainer)
    assert isinstance(trainer.args, SFTConfig)
    assert trainer.args.max_steps == 2
    assert not trainer.args.packing
    for row in rows:
        assert row["labels"] == [-100] * 4 + row["input_ids"][4:6] + [-100] * 2
    contract = import_module("labs.04_llm_finetuning.sft_workflow.batch_contract")
    batch = contract.verify_training_batches(trainer, rows)
    model = trainer.model
    assert isinstance(model, PeftModel)
    frozen = {n: p.detach().clone() for n, p in model.named_parameters() if not p.requires_grad}
    trainable = {n: p.detach().clone() for n, p in model.named_parameters() if p.requires_grad}
    assert frozen
    assert trainable
    assert all("lora_" in n for n in trainable)
    result = exercise_call(
        starter.compare_and_reload, model, tmp_path / "base", tmp_path / "before", batch
    )
    assert result["reload_equal"]
    assert result["max_abs_error"] <= 1e-6
    trained = trainer.train()
    assert torch.isfinite(torch.tensor(trained.training_loss))
    named = dict(model.named_parameters())
    assert all(torch.equal(t, named[n]) for n, t in frozen.items())
    assert any(not torch.equal(t, named[n]) for n, t in trainable.items())
    result = exercise_call(
        starter.compare_and_reload, model, tmp_path / "base", tmp_path / "after", batch
    )
    assert result["reload_equal"]
    assert result["max_abs_error"] <= 1e-6
    assert load_file(str(tmp_path / "after" / "adapter_model.safetensors"))

    # Independently check bytes/reload; the learner's returned booleans are not evidence alone.
    fresh = AutoModelForCausalLM.from_pretrained(
        tmp_path / "base", local_files_only=True, attn_implementation="eager"
    )
    loaded = PeftModel.from_pretrained(fresh, tmp_path / "after", local_files_only=True)
    loaded.eval()
    model.eval()
    with torch.no_grad():
        expected = model(**batch).logits
        actual = loaded(**batch).logits
    assert torch.isfinite(actual).all()
    torch.testing.assert_close(expected, actual, atol=1e-6, rtol=0)
