"""Локальный random encoder: механика inference/save/load, без оценки pretrained качества."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


def make_local_components(num_labels: int = 2) -> tuple[Any, Any]:
    """Construct everything from local values; no from_pretrained Hub identifier."""
    import torch
    from transformers import BertConfig, BertForSequenceClassification, BertTokenizer

    vocabulary = [
        "[PAD]",
        "[UNK]",
        "[CLS]",
        "[SEP]",
        "[MASK]",
        "red",
        "blue",
        "green",
        "square",
        "circle",
        "triangle",
        "small",
        "large",
        "object",
    ]
    tokenizer = BertTokenizer(vocab={word: index for index, word in enumerate(vocabulary)})
    # Dynamic factory boundary: upstream model constructors are not fully typed.
    model_factory: Any = BertForSequenceClassification
    config_factory: Any = BertConfig
    with torch.random.fork_rng():
        torch.manual_seed(17)
        model = model_factory(
            config_factory(
                vocab_size=len(vocabulary),
                hidden_size=16,
                intermediate_size=24,
                num_hidden_layers=2,
                num_attention_heads=2,
                max_position_embeddings=128,
                hidden_dropout_prob=0.0,
                attention_probs_dropout_prob=0.0,
                num_labels=num_labels,
            )
        )
    return model, tokenizer


def run_smoke(directory: Path) -> dict[str, object]:
    """Run a neighboring shape-label inference demonstration, never student tasks."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if directory.exists() and any(directory.iterdir()):
        raise ValueError("smoke destination must be empty")
    model, tokenizer = make_local_components()
    texts = ["red", "large blue square"]
    inputs = tokenizer(texts, padding=True, truncation=True, max_length=8, return_tensors="pt")
    model.eval()
    with torch.inference_mode():
        logits = model(**inputs).logits
    model.save_pretrained(directory, safe_serialization=True)
    tokenizer.save_pretrained(directory)
    restored = AutoModelForSequenceClassification.from_pretrained(
        directory, local_files_only=True, trust_remote_code=False, use_safetensors=True
    ).eval()
    restored_tokenizer = AutoTokenizer.from_pretrained(
        directory, local_files_only=True, trust_remote_code=False
    )
    with torch.inference_mode():
        restored_logits = restored(
            **restored_tokenizer(
                texts, padding=True, truncation=True, max_length=8, return_tensors="pt"
            )
        ).logits
    return {
        "evidence": "LOCAL_RANDOM_ENCODER_SMOKE_ONLY",
        "pretrained_quality": "NOT_RUN",
        "logits_shape": list(logits.shape),
        "padding_tokens": int((inputs["attention_mask"] == 0).sum()),
        "finite_logits": bool(torch.isfinite(logits).all()),
        "reload_max_abs_difference": float((logits - restored_logits).abs().max()),
    }


def main() -> None:
    with TemporaryDirectory(prefix="roadmap-hf-smoke-") as temporary:
        print(json.dumps(run_smoke(Path(temporary) / "checkpoint"), indent=2))


if __name__ == "__main__":
    main()
