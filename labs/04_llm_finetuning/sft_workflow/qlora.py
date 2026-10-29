"""Explicit local-snapshot QLoRA recipe. NOT_RUN until actual CUDA evidence exists."""

import argparse
import importlib.util
import json
import math
import re
from pathlib import Path
from typing import Any


def preflight(args: argparse.Namespace, cuda: Any) -> None:
    if not 1 <= args.max_steps <= 4 or not 8 <= args.max_length <= 256:
        raise ValueError("QLoRA limits: 1..4 steps, 8..256 tokens")
    targets = getattr(args, "target_modules", "q_proj,v_proj").split(",")
    if not targets or any(not re.fullmatch(r"[A-Za-z_]\w*", target) for target in targets):
        raise ValueError("target-modules must be comma-separated nonempty module names")
    if not args.base.is_dir() or not args.tokenizer.is_dir() or not args.data.is_file():
        raise ValueError("explicit local base, tokenizer and JSON data are required")
    if args.output.exists():
        raise ValueError("output must be a new directory")
    if not cuda.is_available():
        raise RuntimeError("CUDA unavailable: QLoRA NOT_RUN; CPU is not CUDA evidence")
    if cuda.get_device_capability(0) < (6, 0):
        raise RuntimeError("NF4 requires supported CUDA capability >= 6.0")


def read_training_rows(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not 1 <= len(rows) <= 32:
        raise ValueError("recipe accepts 1..32 already isolated TRAIN conversation rows")
    if any(set(row) != {"messages"} for row in rows):
        raise ValueError("data must contain messages only; prepare separate train data explicitly")
    return rows


def run(args: argparse.Namespace) -> None:
    import torch

    preflight(args, torch.cuda)
    if importlib.util.find_spec("bitsandbytes") is None:
        raise RuntimeError("Install optional --group quantization in a compatible CUDA environment")
    from peft import LoraConfig, PeftModel, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl.trainer.sft_config import SFTConfig
    from trl.trainer.sft_trainer import SFTTrainer

    dataset_type: Any = importlib.import_module("datasets").Dataset

    rows = read_training_rows(args.data)
    tokenizer: Any = AutoTokenizer.from_pretrained(
        args.tokenizer, local_files_only=True, trust_remote_code=False
    )
    if not tokenizer.chat_template or "generation" not in tokenizer.chat_template:
        raise ValueError("template must support assistant token masking")
    for row in rows:
        encoded = tokenizer.apply_chat_template(
            row["messages"], tokenize=True, return_dict=True, return_assistant_tokens_mask=True
        )
        if len(encoded["input_ids"]) > args.max_length or not any(encoded["assistant_masks"]):
            raise ValueError("answer truncation or missing assistant mask is forbidden")
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quantization_type: Any = BitsAndBytesConfig  # upstream constructor is untyped
    quant = quantization_type(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=dtype,
    )
    base = AutoModelForCausalLM.from_pretrained(
        args.base,
        local_files_only=True,
        trust_remote_code=False,
        quantization_config=quant,
        device_map={"": 0},
        dtype=dtype,
    )
    prepare_kbit: Any = prepare_model_for_kbit_training  # upstream is untyped
    base = prepare_kbit(base, use_gradient_checkpointing=True)
    args.output.mkdir(parents=True, exist_ok=False)
    trainer = SFTTrainer(
        model=base,
        processing_class=tokenizer,
        train_dataset=dataset_type.from_list(rows),
        peft_config=LoraConfig(
            r=4,
            lora_alpha=8,
            lora_dropout=0.0,
            target_modules=args.target_modules.split(","),
            task_type="CAUSAL_LM",
        ),
        args=SFTConfig(
            output_dir=str(args.output / "trainer"),
            max_steps=args.max_steps,
            max_length=args.max_length,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=1,
            gradient_checkpointing=True,
            bf16=dtype == torch.bfloat16,
            fp16=dtype == torch.float16,
            packing=False,
            assistant_only_loss=True,
            report_to="none",
            save_strategy="no",
            optim="adamw_torch",
        ),
    )
    trained = trainer.train()
    model = trainer.model
    if not isinstance(model, PeftModel):
        raise TypeError("QLoRA trainer must contain a PEFT model")
    model.save_pretrained(args.output / "adapter", safe_serialization=True)
    _write_status(
        args.output,
        trained.training_loss,
        device=torch.cuda.get_device_name(0),
        steps=args.max_steps,
        max_length=args.max_length,
    )


def _write_status(
    output: Path, training_loss: float, *, device: str, steps: int, max_length: int
) -> None:
    """Write execution evidence only after checking loss and the saved CPU tensors."""
    if not math.isfinite(training_loss):
        raise ValueError("QLoRA requires finite training loss")
    import torch
    from safetensors.torch import load_file

    try:
        tensors = load_file(str(output / "adapter" / "adapter_model.safetensors"), device="cpu")
    except OSError as exc:
        raise ValueError("QLoRA requires nonempty finite saved adapter tensors") from exc
    if not tensors or any(
        tensor.numel() == 0 or not torch.isfinite(tensor).all() for tensor in tensors.values()
    ):
        raise ValueError("QLoRA requires nonempty finite saved adapter tensors")
    (output / "status.json").write_text(
        json.dumps(
            {
                "status": "CUDA_RECIPE_EXECUTED_REQUIRES_REVIEW",
                "device": device,
                "training_loss": training_loss,
                "steps": steps,
                "max_length": max_length,
                "learner_credit": False,
                "pretrained_quality": "NOT_EVALUATED",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("base", "tokenizer", "data", "output"):
        parser.add_argument(f"--{field}", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--target-modules", default="q_proj,v_proj")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
