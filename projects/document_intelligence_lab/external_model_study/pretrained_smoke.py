"""Explicit author pretrained-inference smoke, not a completed external-model study.

Only run() can identify pinned pretrained resources. checkpoint_smoke() also works
with test-owned random weights and makes no pretrained-quality claim by itself.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from projects.external_tabular.evidence import json_bytes

from ..contracts import normalize_document
from .protocol import LAB


def checkpoint_smoke(model: Any, tokenizer: Any, texts: list[str], output: Path) -> dict[str, Any]:
    """Author API trace only: masked pooling, safetensors, local reload."""
    import torch

    transformers = importlib.import_module("transformers")
    if output.exists() and any(output.iterdir()):
        raise ValueError("checkpoint smoke output must be empty")
    batch = tokenizer(texts, padding=True, truncation=True, max_length=64, return_tensors="pt")
    model.eval()
    with torch.inference_mode():
        hidden = model(**batch).last_hidden_state
        mask = batch["attention_mask"].unsqueeze(-1).to(hidden.dtype)
        mean = (hidden * mask).sum(1) / mask.sum(1).clamp_min(1)
        vectors = torch.nn.functional.normalize(mean, p=2, dim=1)
    model.save_pretrained(output, safe_serialization=True)
    tokenizer.save_pretrained(output)
    restored = transformers.AutoModel.from_pretrained(
        output, local_files_only=True, trust_remote_code=False, use_safetensors=True
    ).eval()
    with torch.inference_mode():
        reloaded_hidden = restored(**batch).last_hidden_state
    return {
        "texts": len(texts),
        "embedding_shape": list(vectors.shape),
        "finite": bool(torch.isfinite(vectors).all()),
        "padding_tokens": int((batch["attention_mask"] == 0).sum()),
        "reload_max_abs_difference": float((hidden - reloaded_hidden).abs().max()),
        "quality_evaluation": "NOT_RUN",
    }


def run(cache: Path, output: Path) -> dict[str, Any]:
    # Check source hashes before importing heavyweight libraries or creating output.
    resource = importlib.import_module(LAB + ".download").verify_cache(cache)
    if output.exists() and any(output.iterdir()):
        raise ValueError("author smoke output must be empty")
    transformers = importlib.import_module("transformers")
    starter = importlib.import_module(LAB + ".starter")
    csv_path = cache / "dataset" / resource["dataset"]["files"][0]["filename"]
    selected = {}
    with csv_path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["intent"] in starter.LABELS and row["intent"] not in selected:
                text = normalize_document(row["instruction"])
                selected[row["intent"]] = starter.Document(
                    row_id=hashlib.sha256(text.encode()).hexdigest(),
                    text=text,
                    label=starter.LABELS.index(row["intent"]),
                )
    if set(selected) != set(starter.LABELS):
        raise ValueError("source lacks one of the four expected intents")
    documents = [selected[label] for label in starter.LABELS]
    model = transformers.AutoModel.from_pretrained(
        cache / "model", local_files_only=True, trust_remote_code=False, use_safetensors=True
    )
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        cache / "model", local_files_only=True, trust_remote_code=False
    )
    result = checkpoint_smoke(
        model, tokenizer, [row.text for row in documents], output / "checkpoint"
    )
    result.update(
        {
            "evidence": "AUTHOR_PRETRAINED_INFERENCE_SMOKE_ONLY",
            "model": resource["model"],
            "dataset": resource["dataset"],
            "records": [asdict(row) for row in documents],
            "learner_credit": "NOT_GRANTED",
        }
    )
    (output / "author-smoke.json").write_bytes(json_bytes(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Four-row pinned pretrained author inference only")
    parser.add_argument("--cache", type=Path, default=Path(".cache/roadmap-huggingface"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.cache, args.output))


if __name__ == "__main__":
    main()
