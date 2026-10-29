"""Explicit max-four-step TRL/PEFT mechanics. No pretrained quality or learner credit."""

import argparse
import importlib.metadata
import json
import math
from pathlib import Path
from typing import Any


def run(output: Path, steps: int = 2) -> dict[str, Any]:
    if not 1 <= steps <= 4:
        raise ValueError("author smoke permits 1..4 optimizer steps")
    output.mkdir(parents=True, exist_ok=False)
    import torch
    from peft import LoraConfig, PeftModel
    from safetensors.torch import load_file
    from transformers import AutoModelForCausalLM, default_data_collator
    from trl.trainer.sft_config import SFTConfig
    from trl.trainer.sft_trainer import SFTTrainer

    dataset_type: Any = importlib.import_module("datasets").Dataset

    from .author_fixture import CORPUS, author_training_rows, tiny_components

    torch.set_num_threads(1)
    torch.manual_seed(17)
    base, tokenizer = tiny_components()
    base.save_pretrained(output / "base", safe_serialization=True)
    tokenizer.save_pretrained(output / "base")
    rows = author_training_rows(tokenizer)
    trainer = SFTTrainer(
        model=base,
        processing_class=tokenizer,
        train_dataset=dataset_type.from_list(rows),
        data_collator=default_data_collator,
        args=SFTConfig(
            output_dir=str(output / "trainer"),
            use_cpu=True,
            bf16=False,
            fp16=False,
            gradient_checkpointing=False,
            max_steps=steps,
            per_device_train_batch_size=2,
            learning_rate=0.01,
            optim="adamw_torch",
            report_to="none",
            save_strategy="no",
            logging_strategy="no",
            disable_tqdm=True,
            packing=False,
            remove_unused_columns=False,
            dataset_kwargs={"skip_prepare_dataset": True},
            max_length=16,
            dataloader_pin_memory=False,
            seed=17,
        ),
        peft_config=LoraConfig(
            r=2,
            lora_alpha=4,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.0,
            bias="none",
            task_type="CAUSAL_LM",
        ),
    )
    model = trainer.model
    if not isinstance(model, PeftModel):
        raise TypeError("author smoke requires a PEFT model")
    frozen = {n: p.detach().clone() for n, p in model.named_parameters() if not p.requires_grad}
    adapters = {n: p.detach().clone() for n, p in model.named_parameters() if p.requires_grad}
    batch = default_data_collator(rows)
    # Independently verify causal shift: logits at t-1 predict labels at t.
    model.eval()
    with torch.no_grad():
        result = model(**batch)
        manual = torch.nn.functional.cross_entropy(
            result.logits[:, :-1].reshape(-1, result.logits.shape[-1]),
            batch["labels"][:, 1:].reshape(-1),
            ignore_index=-100,
        )
        torch.testing.assert_close(result.loss, manual)
    trained = trainer.train()
    assert math.isfinite(trained.training_loss)
    current = dict(model.named_parameters())
    assert all(torch.equal(before, current[n]) for n, before in frozen.items())
    assert all(current[n].grad is None for n in frozen)
    changed = sum(not torch.equal(before, current[n]) for n, before in adapters.items())
    assert changed > 0
    model.save_pretrained(str(output / "adapter"), safe_serialization=True)
    tensors = load_file(str(output / "adapter" / "adapter_model.safetensors"))
    assert tensors
    assert all(torch.isfinite(t).all() for t in tensors.values())
    fresh = AutoModelForCausalLM.from_pretrained(
        output / "base", local_files_only=True, attn_implementation="eager"
    )
    reloaded = PeftModel.from_pretrained(fresh, output / "adapter", local_files_only=True)
    model.eval()
    reloaded.eval()
    with torch.no_grad():
        expected = model(**batch).logits
        actual = reloaded(**batch).logits
    assert torch.isfinite(actual).all()
    torch.testing.assert_close(expected, actual, rtol=0, atol=0)
    report = {
        "origin": "AUTHOR",
        "evidence_kind": "RANDOM_MECHANISM_ONLY",
        "review_status": "NO_LEARNER_CREDIT",
        "device": "cpu",
        "steps": steps,
        "train_ids": [r["id"] for r in CORPUS[:2]],
        "heldout_ids": [r["id"] for r in CORPUS[2:]],
        "training_loss": trained.training_loss,
        "base_unchanged": True,
        "adapter_changed_count": changed,
        "reload_equal": True,
        "causal_mask_loss_equal": True,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "trl", "peft", "datasets")
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.steps), indent=2))


if __name__ == "__main__":
    main()
