"""Pinned external-data and real-pretrained evidence, checked entirely from local bytes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from projects.external_tabular.evidence import (
    artifact_path,
    check_equal,
    finite,
    nonempty,
    read_json,
    sha256,
    validate_bundle,
)

from ..contracts import normalize_document, validate_dataset, validate_splits

LAB = "labs.02_huggingface_models"


def validate_pretrained_identity(identity: object) -> None:
    expected = importlib.import_module(LAB + ".download").resource_manifest()["model"]
    check_equal(identity, expected, "pinned pretrained model/revision/files/license")


def validate_source_records(data: dict[str, Any], raw: Path, splits: dict[str, Any]) -> None:
    """Reuse the Document Intelligence content/group/split contracts."""
    lab = importlib.import_module(LAB + ".starter")
    spec = importlib.import_module(LAB + ".download").resource_manifest()["dataset"]
    if sha256(raw) != spec["files"][0]["sha256"]:
        raise ValueError("raw external dataset differs from pinned CSV")
    by_content: dict[str, set[int]] = {}
    with raw.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            if row.get("intent") in lab.LABELS:
                if row.get("category") != "ACCOUNT":
                    raise ValueError("raw selected intent has invalid category")
                text = normalize_document(row["instruction"])
                by_content.setdefault(text, set()).add(lab.LABELS.index(row["intent"]))
    converted = []
    if data.get("classes") != [0, 1, 2, 3]:
        raise ValueError("text project requires four ACCOUNT intent IDs")
    for row in data["records"]:
        text = nonempty(row.get("text"), "text")
        if normalize_document(text) != text or by_content.get(text) != {row["label"]}:
            raise ValueError("saved text/label must reproduce unambiguous normalized source rows")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if row["row_id"] != digest:
            raise ValueError("row ID must equal normalized content SHA-256")
        converted.append(
            {
                "row_id": row["row_id"],
                "text": text,
                "label": lab.LABELS[row["label"]],
                "source_id": spec["id"],
                "group_id": row["group_id"],
                "content_sha256": digest,
            }
        )
    dataset = validate_dataset(
        {"schema_version": 1, "labels": list(lab.LABELS), "records": converted}
    )
    validate_splits(splits, dataset)


def validate_tokenizer_semantics(base: Path, adapted: Path) -> None:
    """Compare loaded tokenization pipelines and evaluation-relevant auxiliary settings.

    The evaluation call supplies padding=True, truncation=True and max_length. Its
    persisted backend padding/truncation cache is therefore not tokenizer identity.
    Vocabulary, added tokens, normalization, pre/post-processing and decoding remain
    compared in full. Loaded attributes also include settings from auxiliary JSON.
    """
    transformers = importlib.import_module("transformers")

    def semantics(directory: Path) -> dict[str, Any]:
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            directory, local_files_only=True, trust_remote_code=False
        )
        backend = getattr(tokenizer, "backend_tokenizer", None)
        if backend is None:
            raise ValueError("tokenizer must retain the pinned fast-tokenizer implementation")
        pipeline = json.loads(backend.to_str())
        # Replaced by explicit arguments on every evaluation call, including default
        # stride/pad_to_multiple_of. Direction and special IDs below remain significant.
        pipeline.pop("padding", None)
        pipeline.pop("truncation", None)
        attributes = (
            "padding_side",
            "truncation_side",
            "model_input_names",
            "pad_token_type_id",
            "split_special_tokens",
            "do_lower_case",
            "clean_up_tokenization_spaces",
            "add_bos_token",
            "add_eos_token",
        )
        return {
            "implementation": type(tokenizer).__name__,
            "pipeline": pipeline,
            "special_tokens": tokenizer.special_tokens_map,
            "settings": {name: getattr(tokenizer, name, None) for name in attributes},
        }

    check_equal(semantics(adapted), semantics(base), "effective adapted tokenizer semantics")


def validate_checkpoint_inventory(root: Path, result: dict[str, Any]) -> tuple[Path, Path]:
    manifest = result["manifest"]
    refs = manifest["artifacts"]
    files = result["files"]
    model = importlib.import_module(LAB + ".download").resource_manifest()["model"]
    # Base filenames and pinned hashes anchor the actual pretrained bytes, not a free-text claim.
    for spec in model["files"]:
        logical = "base/" + spec["filename"]
        if logical not in refs or sha256(files[logical]) != spec["sha256"]:
            raise ValueError("pretrained base artifact missing or differs from pinned weights")
        if files[logical].stat().st_size != spec["size_bytes"]:
            raise ValueError("pretrained base file size differs")
    for name in ("model.safetensors", "config.json", "tokenizer.json"):
        if "adapted/" + name not in files:
            raise ValueError("adapted checkpoint requires actual safetensors/config/tokenizer")
    for prefix in ("base", "adapted"):
        entries = [ref for logical, ref in refs.items() if logical.startswith(prefix + "/")]
        for entry in entries:
            if not entry["path"].startswith(prefix + "/"):
                raise ValueError("checkpoint files must be inside their named directory")
        directory = root / prefix
        # The loader may read auxiliary files too: disallow unmanifested files and symlinks.
        actual = {path.resolve() for path in directory.rglob("*") if path.is_file()}
        expected = {artifact_path(root, entry["path"]) for entry in entries}
        if actual != expected or any(path.is_symlink() for path in directory.rglob("*")):
            raise ValueError("checkpoint contains unmanifested or symlinked files")
    validate_tokenizer_semantics(root / "base", root / "adapted")
    return root / "base", root / "adapted"


def replay_methods(
    result: dict[str, Any], base: Path, adapted: Path, config: dict[str, Any]
) -> None:
    """Recompute all three methods; never load pickle or make network calls."""
    import torch
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    transformers = importlib.import_module("transformers")

    starter = importlib.import_module(LAB + ".starter")
    rows = {row["row_id"]: row for row in result["data"]["records"]}
    train, test = result["splits"]["train"], result["splits"]["test"]
    train_text = [rows[row_id]["text"] for row_id in train]
    test_text = [rows[row_id]["text"] for row_id in test]
    labels = [rows[row_id]["label"] for row_id in train]
    methods = result["evaluation"]["methods"]
    linear = make_pipeline(
        TfidfVectorizer(), LogisticRegression(max_iter=300, random_state=config["seed"])
    ).fit(train_text, labels)
    check_equal(
        [int(x) for x in linear.predict(test_text)],
        methods["tfidf_linear"]["predictions"],
        "replayed TF-IDF predictions",
    )
    encoder = transformers.AutoModel.from_pretrained(
        base, local_files_only=True, trust_remote_code=False, use_safetensors=True
    ).eval()
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        base, local_files_only=True, trust_remote_code=False
    )

    def embeddings(texts: list[str]) -> Any:
        batches = []
        with torch.inference_mode():
            for offset in range(0, len(texts), config["batch_size"]):
                inputs = starter.encode_batch(
                    tokenizer,
                    texts[offset : offset + config["batch_size"]],
                    max_length=config["max_length"],
                )
                batches.append(
                    starter.masked_mean_pool(
                        encoder(**inputs).last_hidden_state, inputs["attention_mask"]
                    )
                )
        return torch.cat(batches).cpu().numpy()

    frozen = LogisticRegression(max_iter=300, random_state=config["seed"])
    frozen.fit(embeddings(train_text), labels)
    check_equal(
        [int(x) for x in frozen.predict(embeddings(test_text))],
        methods["frozen_embeddings"]["predictions"],
        "replayed frozen predictions",
    )
    restored = transformers.AutoModelForSequenceClassification.from_pretrained(
        adapted, local_files_only=True, trust_remote_code=False, use_safetensors=True
    ).eval()
    base_state = encoder.state_dict()
    adapted_state = restored.base_model.state_dict()
    last_prefix = f"encoder.layer.{len(encoder.encoder.layer) - 1}."
    changed_last = False
    for name, tensor in base_state.items():
        if name not in adapted_state:
            raise ValueError("adapted encoder architecture differs from pinned base")
        equal = torch.equal(tensor, adapted_state[name])
        if name.startswith(last_prefix):
            changed_last |= not equal
        elif not equal:
            raise ValueError("adaptation changed parameters outside the final encoder block")
    if not changed_last:
        raise ValueError("adapted model did not update the real pretrained encoder")
    actual = importlib.import_module(LAB + ".protocol").checkpoint_predictions(
        adapted, test_text, batch_size=config["batch_size"], max_length=config["max_length"]
    )
    check_equal(actual, methods["adapted_encoder"]["predictions"], "replayed adapted predictions")


def validate_submission(root: Path) -> dict[str, Any]:
    result = validate_bundle(root, project_id="document-external-model-study")
    study = read_json(result["files"]["study"])
    validate_pretrained_identity(study.get("model"))
    expected_source = importlib.import_module(LAB + ".download").resource_manifest()["dataset"]
    check_equal(study.get("dataset"), expected_source, "pinned external dataset identity")
    validate_source_records(result["data"], result["files"]["raw"], result["splits"])
    for field in (
        "feature_availability",
        "leakage_audit",
        "split_rationale",
        "selection_rule",
        "error_analysis",
        "limitations",
        "transfer_question",
    ):
        nonempty(study.get(field), field)
    if study.get("preprocessing") != "nfkc-casefold-space-v1":
        raise ValueError("preprocessing differs from lab contract")
    config = study.get("config", {})
    if type(config.get("seed")) is not int or config["seed"] < 0:
        raise ValueError("seed must be nonnegative integer")
    for key in ("batch_size", "max_length", "max_steps"):
        if type(config.get(key)) is not int or config[key] < 1:
            raise ValueError(f"positive integer {key} required")
    if not finite(config.get("learning_rate")) or config["learning_rate"] <= 0:
        raise ValueError("positive finite learning_rate required")
    history = study.get("training_history", {})
    losses = history.get("train_losses")
    if (
        not isinstance(losses, list)
        or len(losses) != config["max_steps"]
        or not all(finite(loss) and loss >= 0 for loss in losses)
    ):
        raise ValueError("training history must preserve measured loss for each optimizer step")
    if history.get("validation_count") != len(result["splits"]["validation"]) or not finite(
        history.get("validation_loss")
    ):
        raise ValueError("training history requires complete validation measurement")
    if study.get("selection", {}).get("used_split") != "validation":
        raise ValueError("model selection must use validation")
    base, adapted = validate_checkpoint_inventory(root, result)
    replay_methods(result, base, adapted, config)
    return {
        "technical_status": "VERIFIED",
        "project_id": "document-external-model-study",
        "human_review": "REQUIRED",
        "authorship": "NOT_AUTOMATICALLY_VERIFIED",
        "replayed_methods": sorted(result["evaluation"]["methods"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline replay of real pretrained-model evidence")
    parser.add_argument("submission", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_submission(args.submission), indent=2))


if __name__ == "__main__":
    main()
