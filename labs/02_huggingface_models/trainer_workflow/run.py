"""Explicit local learner runner; no network/download or training on import."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import starter
from .protocol import (
    RunConfig,
    tokenizer_fingerprint,
    validate_model_mapping,
    validate_saved_artifact,
    validate_splits,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/trainer-learner"))
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--steps", type=int, default=2)
    args = parser.parse_args()
    if not args.snapshot.is_dir() or not (args.snapshot / "model.safetensors").is_file():
        raise ValueError("explicit local safetensors snapshot required")
    if args.output.exists():
        raise ValueError("output must be a new directory")
    payload = json.loads(args.dataset.read_text(encoding="utf-8"))
    labels = {int(k): v for k, v in payload["id2label"].items()}
    validate_splits(payload["splits"], labels)
    # Metadata is an auditable claim, verified manually against the local snapshot.
    if not payload.get("dataset_source") or not payload.get("model_source"):
        raise ValueError("dataset_source and model_source provenance required")
    review = args.review.read_text(encoding="utf-8").strip()
    if not review:
        raise ValueError("human annotation/domain review required")
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise SystemExit("Install optional libraries: uv sync --group trainer") from exc
    torch.set_num_threads(1)
    tokenizer = AutoTokenizer.from_pretrained(
        args.snapshot, local_files_only=True, trust_remote_code=False
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        args.snapshot, local_files_only=True, trust_remote_code=False, use_safetensors=True
    )
    validate_model_mapping(model.config.id2label, model.config.label2id, labels)
    config = RunConfig(max_steps=args.steps)
    result = starter.train_model(
        model, tokenizer, payload["splits"], args.output, config, resume_from_checkpoint=args.resume
    )
    result["tokenizer_identity"] = tokenizer_fingerprint(tokenizer)
    validate_saved_artifact(
        result["checkpoint_path"],
        "sequence",
        result["model_identity"],
        result["tokenizer_identity"],
    )
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
