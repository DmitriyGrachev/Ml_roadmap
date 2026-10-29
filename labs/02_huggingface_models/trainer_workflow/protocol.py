"""Offline data and budget contracts; importing never starts training."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunConfig:
    max_steps: int = 2
    batch_size: int = 2
    max_length: int = 32
    learning_rate: float = 0.0005
    seed: int = 17

    def __post_init__(self) -> None:
        for name in ("max_steps", "batch_size", "max_length", "seed"):
            value = getattr(self, name)
            if type(value) is not int or value < (0 if name == "seed" else 1):
                raise ValueError(f"invalid {name}")
        if self.max_steps > 100 or self.max_length < 2:
            raise ValueError("local budget: max_steps <= 100 and max_length >= 2")
        if (
            isinstance(self.learning_rate, bool)
            or not math.isfinite(self.learning_rate)
            or self.learning_rate <= 0
        ):
            raise ValueError("invalid learning_rate")


def validate_splits(
    splits: Mapping[str, Sequence[Mapping[str, Any]]], labels: Mapping[int, str]
) -> None:
    if set(splits) != {"train", "validation", "test"}:
        raise ValueError("expected train/validation/test splits")
    if (
        not labels
        or set(labels) != set(range(len(labels)))
        or len(set(labels.values())) != len(labels)
    ):
        raise ValueError("invalid label mapping")
    seen: set[str] = set()
    for rows in splits.values():
        if not rows:
            raise ValueError("empty split")
        for row in rows:
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id:
                raise ValueError("invalid id")
            if row_id in seen:
                raise ValueError("split overlap or duplicate id")
            seen.add(row_id)
            if not isinstance(row.get("text"), str) or not row["text"].strip():
                raise ValueError("empty text")
            if type(row.get("label")) is not int or row["label"] not in labels:
                raise ValueError("label outside model mapping")


def validate_model_mapping(
    id2label: Mapping[int, str], label2id: Mapping[str, int], expected: Mapping[int, str]
) -> None:
    if dict(id2label) != dict(expected) or dict(label2id) != {v: k for k, v in expected.items()}:
        raise ValueError("model label mapping mismatch")


def model_fingerprint(model: Any) -> str:
    """Hash actual parameter names/bytes, matching the documented learner format."""
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def tokenizer_fingerprint(tokenizer: Any) -> str:
    """Hash vocabulary, normalizer and special-token semantics, not local paths."""
    backend = json.loads(tokenizer.backend_tokenizer.to_str())
    # These fields are transient batch call settings, not saved model semantics.
    backend.pop("padding", None)
    backend.pop("truncation", None)
    payload = {
        "backend": backend,
        "special_tokens": tokenizer.special_tokens_map,
        "padding_side": tokenizer.padding_side,
        "truncation_side": tokenizer.truncation_side,
        "model_max_length": tokenizer.model_max_length,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def validate_saved_artifact(
    checkpoint: str | Path, kind: str, identity: str, tokenizer_identity: str
) -> None:
    """Reload a declared safe artifact locally; no training or download fallback."""
    path = Path(checkpoint)
    required = ("model.safetensors", "config.json", "tokenizer.json", "tokenizer_config.json")
    if not path.is_dir() or any(not (path / name).is_file() for name in required):
        raise ValueError("retained checkpoint model and tokenizer files required")
    if kind not in {"sequence", "token"}:
        raise ValueError("unsupported checkpoint kind")
    transformers = import_module("transformers")
    constructor = (
        transformers.AutoModelForSequenceClassification
        if kind == "sequence"
        else transformers.AutoModelForTokenClassification
    )
    model = constructor.from_pretrained(
        path, local_files_only=True, trust_remote_code=False, use_safetensors=True
    ).eval()
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        path, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    if not identity or model_fingerprint(model) != identity:
        raise ValueError("saved model fingerprint differs from report")
    if not tokenizer_identity or tokenizer_fingerprint(tokenizer) != tokenizer_identity:
        raise ValueError("saved tokenizer fingerprint differs from report")
    inputs = tokenizer("Ada visits Rome.", return_tensors="pt", truncation=True, max_length=12)
    torch = import_module("torch")
    with torch.inference_mode():
        logits = model(**inputs).logits
    if not bool(torch.isfinite(logits).all()):
        raise ValueError("checkpoint/tokenizer inference is nonfinite")
