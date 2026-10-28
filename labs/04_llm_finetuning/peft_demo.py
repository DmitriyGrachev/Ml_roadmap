"""Offline CPU author experiment: random tiny causal Transformer + actual PEFT LoRA.

Inference checkpoint only; neither pretrained SFT nor a training-resume checkpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, TypedDict

# Set before importing Hub consumers; every loader also requires local_files_only.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import torch
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from safetensors.torch import load_file, save_file
from transformers import LlamaConfig, LlamaForCausalLM

causal_targets = importlib.import_module("labs.04_llm_finetuning.sft_contract").causal_targets

# An explicit whitespace vocabulary, including a tiny fixed template. No tokenizer download.
VOCAB = [
    "<pad>",
    "<bos>",
    "<eos>",
    "repeat",
    "<answer>",
    "amber",
    "birch",
    "coral",
    "now",
    "dune",
    "elm",
    "fern",
    "grove",
]
EXAMPLES = [
    {"id": "author-train-01", "split": "train", "prompt": "repeat amber", "answer": "amber"},
    {"id": "author-train-02", "split": "train", "prompt": "now repeat birch", "answer": "birch"},
    {"id": "author-train-03", "split": "train", "prompt": "repeat coral", "answer": "coral"},
    {"id": "author-train-04", "split": "train", "prompt": "repeat amber now", "answer": "amber"},
    {"id": "author-val-01", "split": "validation", "prompt": "repeat now dune", "answer": "dune"},
    {"id": "author-val-02", "split": "validation", "prompt": "now repeat elm", "answer": "elm"},
    {"id": "author-test-01", "split": "test", "prompt": "repeat now fern", "answer": "fern"},
    {"id": "author-test-02", "split": "test", "prompt": "repeat grove now", "answer": "grove"},
]


class TrainingConfig(TypedDict):
    seed: int
    steps: int
    learning_rate: float
    rank: int
    alpha: int
    max_new_tokens: int
    optimizer: str
    weight_decay: float


TRAINING: TrainingConfig = {
    "seed": 17,
    "steps": 24,
    "learning_rate": 0.03,
    "rank": 4,
    "alpha": 8,
    "max_new_tokens": 3,
    "optimizer": "AdamW",
    "weight_decay": 0.0,
}
REQUIRED_FILES = (
    "base/model.safetensors",
    "base/config.json",
    "base/generation_config.json",
    "adapter/adapter_model.safetensors",
    "adapter/adapter_config.json",
    "adapter/README.md",
    "vocab.json",
    "data.json",
    "training_config.json",
    "expected.safetensors",
    "expected.json",
    "source_identity.json",
)


def configure_cpu() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(int(TRAINING["seed"]))


def make_base() -> Any:
    config = LlamaConfig(
        vocab_size=len(VOCAB),
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=1,
        num_attention_heads=4,
        num_key_value_heads=2,
        max_position_embeddings=32,
        attention_dropout=0.0,
        initializer_range=0.02,
        pad_token_id=0,
        bos_token_id=1,
        eos_token_id=2,
        tie_word_embeddings=False,
        use_cache=False,
    )
    config._attn_implementation = "eager"
    # Transformers' decorated constructor is untyped; keep this boundary explicit.
    model_type: Any = LlamaForCausalLM
    return model_type(config).to(device="cpu", dtype=torch.float32)


def prompt_ids(example: dict[str, str]) -> list[int]:
    return [1, *(VOCAB.index(word) for word in example["prompt"].split()), 4]


def make_batch(examples: list[dict[str, str]]) -> dict[str, torch.Tensor]:
    sequences, labels, masks = [], [], []
    for example in examples:
        prompt = prompt_ids(example)
        answer = [VOCAB.index(word) for word in example["answer"].split()] + [2]
        sequences.append(prompt + answer)
        labels.append([-100] * len(prompt) + answer)
    width = max(map(len, sequences))
    for ids, targets in zip(sequences, labels, strict=True):
        padding = width - len(ids)
        masks.append([1] * len(ids) + [0] * padding)
        ids.extend([0] * padding)
        targets.extend([-100] * padding)
        causal_targets(ids, masks[-1], targets)
    return {
        "input_ids": torch.tensor(sequences),
        "attention_mask": torch.tensor(masks),
        "labels": torch.tensor(labels),
    }


def evaluate(model: Any, examples: list[dict[str, str]]) -> tuple[dict[str, Any], torch.Tensor]:
    model.eval()
    batch = make_batch(examples)
    predictions = []
    with torch.inference_mode():
        result = model(**batch)
        for example in examples:
            ids = prompt_ids(example)
            generated = []
            for _ in range(int(TRAINING["max_new_tokens"])):
                inputs = torch.tensor([ids])
                logits = model(input_ids=inputs, attention_mask=torch.ones_like(inputs)).logits
                token = int(logits[0, -1].argmax())
                ids.append(token)
                generated.append(token)
                if token == 2:
                    break
            predictions.append(
                {
                    "id": example["id"],
                    "token_ids": generated,
                    "tokens": [VOCAB[token] for token in generated],
                }
            )
    return {
        "loss": float(result.loss),
        "target_tokens": int((batch["labels"] != -100).sum()),
        "predictions": predictions,
    }, result.logits.detach().clone()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_identity() -> dict[str, str]:
    return {
        name: digest(Path(__file__).with_name(name)) for name in ("peft_demo.py", "sft_contract.py")
    }


def load_bundle(output: Path) -> Any:
    """Validate our known file set before local deserialization; not an authenticity signature."""
    if output.is_symlink() or output.is_junction():
        raise ValueError("bundle identity requires a real directory")
    output = output.resolve(strict=True)
    for directory in ("base", "adapter"):
        folder = output / directory
        expected_names = {
            Path(name).name for name in REQUIRED_FILES if name.startswith(directory + "/")
        }
        if folder.is_symlink() or folder.is_junction() or not folder.is_dir():
            raise ValueError(f"bundle identity requires a real {directory} directory")
        if {path.name for path in folder.iterdir()} != expected_names:
            raise ValueError(f"bundle inventory mismatch: {directory}")
    identity = output / "identity.json"
    if identity.is_symlink() or identity.is_junction():
        raise ValueError("bundle identity requires a real manifest file")
    manifest = json.loads(identity.read_text(encoding="utf-8"))
    if set(manifest) != set(REQUIRED_FILES):
        raise ValueError("bundle identity file set mismatch")
    for relative in REQUIRED_FILES:
        path = output / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or path.is_junction()
            or digest(path) != manifest[relative]
        ):
            raise ValueError(f"bundle identity mismatch: {relative}")
    if json.loads((output / "vocab.json").read_text(encoding="utf-8")) != VOCAB:
        raise ValueError("vocabulary identity incompatible with this demo")
    if json.loads((output / "data.json").read_text(encoding="utf-8")) != EXAMPLES:
        raise ValueError("data identity incompatible with this demo")
    if json.loads((output / "training_config.json").read_text(encoding="utf-8")) != TRAINING:
        raise ValueError("training configuration identity incompatible with this demo")
    if (
        json.loads((output / "source_identity.json").read_text(encoding="utf-8"))
        != source_identity()
    ):
        raise ValueError("source identity incompatible with this demo")
    base = LlamaForCausalLM.from_pretrained(
        str(output / "base"),
        local_files_only=True,
        attn_implementation="eager",
        dtype=torch.float32,
    )
    model = PeftModel.from_pretrained(
        base, str(output / "adapter"), local_files_only=True, is_trainable=False
    )
    model.eval()
    return model


def verify_bundle(output: Path) -> dict[str, Any]:
    configure_cpu()
    model = load_bundle(output)
    expected = json.loads((output / "expected.json").read_text(encoding="utf-8"))
    reference = load_file(str(output / "expected.safetensors"), device="cpu")
    logits_equal, predictions_equal = True, True
    for split in ("validation", "test"):
        observed, logits = evaluate(model, [e for e in EXAMPLES if e["split"] == split])
        logits_equal = logits_equal and torch.equal(reference[split], logits)
        predictions_equal = predictions_equal and observed == expected[split]
    if not logits_equal or not predictions_equal:
        raise ValueError("reload parity failed")
    return {
        "logits_equal": logits_equal,
        "predictions_equal": predictions_equal,
        "device": "cpu",
        "mode": "eval",
        "versions": versions(),
    }


def versions() -> dict[str, str]:
    return {
        name: importlib.metadata.version(name)
        for name in ("torch", "transformers", "peft", "safetensors")
    }


def loss_svg(output: Path, history: list[dict[str, Any]]) -> None:
    """Plot measured losses without another optional dependency."""
    low = min(float(row["train_loss_before_step"]) for row in history)
    high = max(float(row["train_loss_before_step"]) for row in history)
    span = max(high - low, 1e-6)
    points = " ".join(
        f"{50 + i * 480 / (len(history) - 1):.2f},"
        f"{180 - (float(row['train_loss_before_step']) - low) / span * 130:.2f}"
        for i, row in enumerate(history)
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="230" '
        f'viewBox="0 0 600 230"><rect width="600" height="230" fill="white"/>'
        f'<text x="30" y="25" font-family="sans-serif">'
        f"Measured author train loss (before step)</text>"
        f'<path d="M50 45 V180 H540" fill="none" stroke="#555"/>'
        f'<polyline points="{points}" fill="none" stroke="#146c94" stroke-width="2"/>'
        f'<g font-family="sans-serif" font-size="12" fill="#333">'
        f'<text x="4" y="54">{high:.3f}</text><text x="4" y="180">{low:.3f}</text>'
        f'<text x="50" y="200">1</text><text x="510" y="200">{len(history)}</text>'
        f'<text x="220" y="218">optimizer step; not language quality</text></g></svg>'
    )
    (output / "loss.svg").write_text(svg, encoding="utf-8")


def run_experiment(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    output = output.resolve()
    configure_cpu()
    started = time.perf_counter()
    base = make_base()
    base.save_pretrained(output / "base", safe_serialization=True)
    write_json(output / "vocab.json", VOCAB)
    write_json(output / "data.json", EXAMPLES)
    write_json(output / "training_config.json", TRAINING)
    write_json(output / "source_identity.json", source_identity())
    held_out = {
        split: [e for e in EXAMPLES if e["split"] == split] for split in ("validation", "test")
    }
    initial = {split: evaluate(base, examples)[0] for split, examples in held_out.items()}
    model = get_peft_model(
        base,
        LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=int(TRAINING["rank"]),
            lora_alpha=int(TRAINING["alpha"]),
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.0,
            bias="none",
        ),
    )
    frozen = {
        name: p.detach().clone() for name, p in model.named_parameters() if not p.requires_grad
    }
    adapters = {name: p.detach().clone() for name, p in model.named_parameters() if p.requires_grad}
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=float(TRAINING["learning_rate"]),
        weight_decay=0.0,
    )
    train = make_batch([e for e in EXAMPLES if e["split"] == "train"])
    history = []
    for step in range(1, int(TRAINING["steps"]) + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = model(**train).loss
        loss.backward()
        optimizer.step()
        history.append({"step": step, "train_loss_before_step": float(loss.detach())})
    model.eval()
    adapted, reference = {}, {}
    for split, examples in held_out.items():
        adapted[split], reference[split] = evaluate(model, examples)
    model.save_pretrained(str(output / "adapter"), safe_serialization=True)
    save_file(reference, str(output / "expected.safetensors"))
    write_json(output / "expected.json", adapted)
    identities = {relative: digest(output / relative) for relative in REQUIRED_FILES}
    write_json(output / "identity.json", identities)
    # Separate interpreter: no live model, RNG state, optimizer, or Python globals are reused.
    child = subprocess.run(
        [sys.executable, "-m", "labs.04_llm_finetuning.peft_demo", "--verify", str(output)],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    named = dict(model.named_parameters())
    report = {
        "evidence_kind": "offline-random-transformer-peft-author-mechanism",
        "device": "cpu",
        "dtype": "float32",
        "versions": versions(),
        "training_config": TRAINING,
        "initial": initial,
        "adapted": adapted,
        "history": history,
        "artifact_sha256": identities,
        "source_sha256": source_identity(),
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "frozen_parameters": sum(p.numel() for p in model.parameters() if not p.requires_grad),
        "base_unchanged": all(torch.equal(before, named[name]) for name, before in frozen.items()),
        "frozen_gradients_absent": all(named[name].grad is None for name in frozen),
        "changed_adapter_parameters": sum(
            not torch.equal(before, named[name]) for name, before in adapters.items()
        ),
        "fresh_process": json.loads(child.stdout),
        "elapsed_seconds": time.perf_counter() - started,
        "limits": "Random weights; tiny synthetic author data; no pretrained quality claim; "
        "adapter/base bundle supports inference reload, not exact training resume.",
    }
    write_json(output / "report.json", report)
    loss_svg(output, history)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path, help="NEW output directory")
    group.add_argument("--verify", type=Path, help="Verify own local checkpoint in eval mode")
    args = parser.parse_args()
    result = verify_bundle(args.verify) if args.verify is not None else run_experiment(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
