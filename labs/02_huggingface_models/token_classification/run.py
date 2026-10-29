"""Train learner NER only with an explicit local dataset and safetensors snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from importlib import import_module
from pathlib import Path

from . import starter
from .protocol import LABELS, validate_annotations, validate_report_structure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/ner-learner"))
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=2)
    args = parser.parse_args()
    artifact_protocol = import_module("labs.02_huggingface_models.trainer_workflow.protocol")
    artifact_protocol.RunConfig(
        max_steps=args.steps, max_length=args.max_length, batch_size=args.batch_size
    )
    if not args.snapshot.is_dir() or not (args.snapshot / "model.safetensors").is_file():
        raise ValueError("explicit local safetensors snapshot required")
    if args.output.exists():
        raise ValueError("output must be a new directory")
    payload = json.loads(args.dataset.read_text(encoding="utf-8"))
    validate_annotations(payload["splits"])
    if not payload.get("dataset_source") or not payload.get("model_source"):
        raise ValueError("dataset_source and model_source provenance required")
    review = args.review.read_text(encoding="utf-8").strip()
    if not review:
        raise ValueError("human annotation/domain review required")
    try:
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer
    except ImportError as exc:
        raise SystemExit("Install optional libraries: uv sync --group trainer") from exc
    torch.set_num_threads(1)
    tokenizer = AutoTokenizer.from_pretrained(
        args.snapshot, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    if not tokenizer.is_fast:
        raise ValueError("fast tokenizer with word_ids required")
    model = AutoModelForTokenClassification.from_pretrained(
        args.snapshot, local_files_only=True, trust_remote_code=False, use_safetensors=True
    )
    expected = dict(enumerate(LABELS))
    if model.config.id2label != expected or model.config.label2id != {
        v: k for k, v in expected.items()
    }:
        raise ValueError("model label mapping mismatch; prepare explicit mapping/head locally")
    result = starter.train_token_classifier(
        model,
        tokenizer,
        payload["splits"],
        args.output,
        max_steps=args.steps,
        max_length=args.max_length,
        batch_size=args.batch_size,
    )
    result["tokenizer_identity"] = artifact_protocol.tokenizer_fingerprint(tokenizer)
    artifact_protocol.validate_saved_artifact(
        result["checkpoint_path"], "token", result["model_identity"], result["tokenizer_identity"]
    )
    validate_report_structure(result)
    with (args.snapshot / "model.safetensors").open("rb") as source:
        model_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
    result.update(
        evidence="LEARNER_LOCAL_PRETRAINED",
        human_review=review,
        provenance={
            "model_source": payload["model_source"],
            "dataset_source": payload["dataset_source"],
            "snapshot": str(args.snapshot.resolve()),
            "model_sha256": model_sha256,
            "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        },
    )
    args.output.mkdir(parents=True, exist_ok=True)
    report = json.dumps(result, indent=2, allow_nan=False)
    if len(report.encode("utf-8")) > 1_000_000:
        raise ValueError("report exceeds the 1 MB teaching budget")
    (args.output / "report.json").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
