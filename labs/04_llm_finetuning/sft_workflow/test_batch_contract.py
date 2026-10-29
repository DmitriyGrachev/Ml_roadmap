"""Teacher-only CPU batch/loss regressions; no optimization and no learner credit."""

import os
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_SFT") != "1", reason="Explicit ROADMAP_RUN_SFT=1 required"
)


@pytest.mark.parametrize("defect", ["none", "replace_labels", "wrong_loss"])
def test_actual_trl_batch_and_loss_before_optimization(
    tmp_path: Path, defect: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    import torch
    from transformers import default_data_collator
    from trl.trainer.sft_config import SFTConfig
    from trl.trainer.sft_trainer import SFTTrainer

    fixture = import_module("labs.04_llm_finetuning.sft_workflow.author_fixture")
    contract = import_module("labs.04_llm_finetuning.sft_workflow.batch_contract")
    dataset_type: Any = import_module("datasets").Dataset
    torch.set_num_threads(1)
    torch.manual_seed(17)
    model, tokenizer = fixture.tiny_components()
    rows = fixture.author_training_rows(tokenizer)
    for row in rows:
        row["input_ids"] += [0, 0]
        row["attention_mask"] += [0, 0]
        row["labels"] += [-100, -100]

    def collate(batch: Any) -> Any:
        result = default_data_collator(batch)
        if defect == "replace_labels":
            result["labels"] = result["input_ids"].clone()
        return result

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset_type.from_list(list(reversed(rows))),
        data_collator=collate,
        args=SFTConfig(
            output_dir=str(tmp_path / "trainer"),
            use_cpu=True,
            bf16=False,
            gradient_checkpointing=False,
            per_device_train_batch_size=2,
            report_to="none",
            packing=False,
            remove_unused_columns=False,
            dataset_kwargs={"skip_prepare_dataset": True},
            max_length=8,
            dataloader_pin_memory=False,
        ),
    )
    if defect == "wrong_loss":
        # Preserve real batch construction but simulate an incorrect learner loss override.
        def wrong_loss(*args: Any, **kwargs: Any) -> Any:
            return torch.tensor(0.0)

        monkeypatch.setattr(trainer, "compute_loss", wrong_loss)
    before = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
    if defect == "replace_labels":
        with pytest.raises(ValueError, match="actual training batch changed"):
            contract.verify_training_batches(trainer, rows)
    elif defect == "wrong_loss":
        with pytest.raises(AssertionError):
            contract.verify_training_batches(trainer, rows)
    else:
        batch = contract.verify_training_batches(trainer, rows)
        assert batch["labels"].shape == (2, 8)
    assert trainer.state.global_step == 0
    assert trainer.optimizer is None
    assert all(torch.equal(before[name], tensor) for name, tensor in model.state_dict().items())
    assert all(parameter.grad is None for parameter in model.parameters())
