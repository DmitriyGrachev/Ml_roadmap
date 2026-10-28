"""Reuse the existing tiny random HF model; compare artifacts, not pretrained quality."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

from ..artifacts import file_sha256, json_bytes, read_json
from ..contracts import normalize_document
from ..part_a1.demo import run_demo as run_a1
from .protocol import compare, predict_local_encoder, register_checkpoint


def run_demo(output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(output)
    import torch

    hf = importlib.import_module("labs.02_huggingface_models.example")
    run = run_a1(output / "a1")
    baseline_roots = {name: run / name for name in ("rules", "tfidf-linear")}
    reference = read_json(baseline_roots["rules"] / "manifest.json")
    labels = reference["labels"]
    model, tokenizer = hf.make_local_components(num_labels=len(labels))
    model.config.id2label = dict(enumerate(labels))
    model.config.label2id = {label: index for index, label in enumerate(labels)}
    checkpoint = output / "encoder"
    checkpoint.mkdir()
    model.save_pretrained(checkpoint, safe_serialization=True)
    tokenizer.save_pretrained(checkpoint)
    digest = register_checkpoint(
        checkpoint,
        labels=labels,
        dataset_sha256=reference["dataset_sha256"],
        split_sha256=reference["split_sha256"],
        source_revision="local-config-seed-17",
        evidence_kind="teacher-random",
    )
    texts = ["small red circle", "large blue triangle"]
    batch = tokenizer(
        [normalize_document(text) for text in texts],
        padding=True,
        truncation=True,
        max_length=32,
        return_tensors="pt",
    )
    model.eval()
    with torch.inference_mode():
        logits = model(**batch).logits
        expected = [labels[index] for index in logits.argmax(dim=1).tolist()]
    restored = predict_local_encoder(checkpoint, texts, expected_manifest_sha256=digest)
    report = compare(
        {
            name: (root, file_sha256(root / "manifest.json"))
            for name, root in baseline_roots.items()
        },
        checkpoint,
        encoder_manifest_sha256=digest,
        trusted_local_artifacts=True,  # Only the teacher bundles just created above.
    )
    report["reload_parity"] = expected == restored
    report["shapes"] = {
        "input_ids": list(batch["input_ids"].shape),
        "attention_mask": list(batch["attention_mask"].shape),
        "logits": list(logits.shape),
    }
    report["seed"] = 17
    report["training"] = "NOT_RUN: random model from existing HF teacher constructor"
    (output / "comparison.json").write_bytes(json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory only")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.output), indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
