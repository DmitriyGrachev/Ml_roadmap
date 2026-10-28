"""Local encoder bytes and the same cohort; old HF student protocols stay unchanged."""

from __future__ import annotations

import importlib
import platform
from collections.abc import Mapping, Sequence
from importlib.metadata import version
from pathlib import Path
from typing import Any

from roadmap_tools.experiment_evidence import checked_artifact

from ..artifacts import (
    VerifiedBundle,
    file_sha256,
    json_bytes,
    load_trusted_local_classifier,
    predict_documents,
    read_json,
    verify_bundle,
)
from ..contracts import (
    classification_metrics,
    nonempty,
    normalize_document,
    object_value,
    sha256_value,
)

MANIFEST = "encoder-manifest.json"


def _preflight(root: Path, value: object) -> dict[str, Any]:
    manifest = object_value(value, "encoder manifest")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError("unsupported encoder schema")
    for name in ("dataset_sha256", "split_sha256"):
        sha256_value(manifest.get(name), name)
    evidence_kind = manifest.get("evidence_kind")
    if not isinstance(evidence_kind, str) or evidence_kind not in {
        "teacher-random",
        "student-local",
    }:
        raise ValueError("unsupported evidence_kind: no automatic quality claim")
    nonempty(manifest.get("source_revision"), "source_revision")
    labels = manifest.get("labels")
    if not isinstance(labels, list) or len(labels) < 2:
        raise ValueError("labels must be an ordered list")
    for label in labels:
        nonempty(label, "label")
    if len(set(labels)) != len(labels):
        raise ValueError("duplicate labels")
    batch = manifest.get("batch_size")
    length = manifest.get("max_length")
    if type(batch) is not int or not 1 <= batch <= 32:
        raise ValueError("batch_size must be an integer from 1 to 32")
    if type(length) is not int or not 2 <= length <= 512:
        raise ValueError("max_length must be an integer from 2 to 512")
    inventory = object_value(manifest.get("files"), "checkpoint inventory")
    if not {"config.json", "tokenizer.json", "model.safetensors"}.issubset(inventory):
        raise ValueError("checkpoint inventory needs config, tokenizer and safetensors")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != root / MANIFEST
    }
    if set(inventory) != actual:
        raise ValueError("checkpoint inventory differs from present files")
    for name, digest in inventory.items():
        if not name.endswith((".json", ".safetensors", ".txt")):
            raise ValueError("unsupported checkpoint file type")
        checked_artifact(root, name, sha256_value(digest, "file sha256"))
    config = object_value(read_json(root / "config.json"), "model config")
    expected_map = {str(index): label for index, label in enumerate(labels)}
    if config.get("id2label") != expected_map:
        raise ValueError("checkpoint label mapping differs from canonical labels")
    positions = config.get("max_position_embeddings")
    if type(positions) is not int or positions < length:
        raise ValueError("max_length exceeds saved model positions")
    return manifest


def register_checkpoint(
    root: Path,
    *,
    labels: list[str],
    dataset_sha256: str,
    split_sha256: str,
    source_revision: str,
    evidence_kind: str,
    batch_size: int = 2,
    max_length: int = 32,
) -> str:
    """Inventory an operator-selected local checkpoint; never download or overwrite."""
    if (root / MANIFEST).exists():
        raise FileExistsError(root / MANIFEST)
    if not root.is_dir():
        raise ValueError("local checkpoint directory is missing")
    manifest = {
        "schema_version": 1,
        "labels": labels,
        "dataset_sha256": dataset_sha256,
        "split_sha256": split_sha256,
        "source_revision": source_revision,
        "evidence_kind": evidence_kind,
        "batch_size": batch_size,
        "max_length": max_length,
        "files": {
            path.relative_to(root).as_posix(): file_sha256(path)
            for path in sorted(root.rglob("*"))
            if path.is_file()
        },
    }
    _preflight(root, manifest)
    with (root / MANIFEST).open("xb") as destination:
        destination.write(json_bytes(manifest))
    return file_sha256(root / MANIFEST)


def verify_checkpoint(root: Path, *, expected_manifest_sha256: str) -> dict[str, Any]:
    path = checked_artifact(root, MANIFEST, expected_manifest_sha256)
    return _preflight(root, read_json(path))


def predict_local_encoder(
    root: Path,
    texts: Sequence[str],
    *,
    expected_manifest_sha256: str,
) -> list[str]:
    manifest = verify_checkpoint(root, expected_manifest_sha256=expected_manifest_sha256)
    if not texts or len(texts) > 128:
        raise ValueError("provide 1..128 documents per explicit inference call")
    if any(not isinstance(text, str) or not text.strip() or len(text) > 10000 for text in texts):
        raise ValueError("documents must be nonempty text up to 10000 characters")
    # The existing helper enforces local_files_only, safetensors, no remote code, eval/no_grad.
    protocol = importlib.import_module("labs.02_huggingface_models.protocol")
    ids = protocol.checkpoint_predictions(
        root,
        [normalize_document(text) for text in texts],
        batch_size=manifest["batch_size"],
        max_length=manifest["max_length"],
    )
    labels = manifest["labels"]
    if len(ids) != len(texts) or any(
        type(index) is not int or index not in range(len(labels)) for index in ids
    ):
        raise ValueError("encoder output differs from label mapping")
    return [str(labels[index]) for index in ids]


def verify_comparison_inputs(
    baselines: Mapping[str, tuple[Path, str]],
    encoder: Path,
    *,
    encoder_manifest_sha256: str,
) -> tuple[dict[str, VerifiedBundle], dict[str, Any]]:
    """Verify pinned inventory and matching cohorts without loading or running models."""
    if set(baselines) != {"rules", "tfidf-linear"}:
        raise ValueError("comparison requires rules and tfidf-linear bundles")
    bundles = {
        name: verify_bundle(root, expected_manifest_sha256=digest)
        for name, (root, digest) in baselines.items()
    }
    reference = bundles["rules"]
    manifest = verify_checkpoint(encoder, expected_manifest_sha256=encoder_manifest_sha256)
    for candidate in [manifest, *(bundle.manifest for bundle in bundles.values())]:
        if any(
            candidate.get(key) != reference.manifest.get(key)
            for key in ("dataset_sha256", "split_sha256", "labels")
        ):
            raise ValueError("comparison cohort identity differs")
    for name, bundle in bundles.items():
        if bundle.manifest["method"] != name:
            raise ValueError("baseline method identity differs")
    return bundles, manifest


def compare(
    baselines: Mapping[str, tuple[Path, str]],
    encoder: Path,
    *,
    encoder_manifest_sha256: str,
    trusted_local_artifacts: bool = False,
) -> dict[str, Any]:
    """Recompute encoder outputs and compare only matching saved evaluation cohorts."""
    bundles, manifest = verify_comparison_inputs(
        baselines, encoder, encoder_manifest_sha256=encoder_manifest_sha256
    )
    reference = bundles["rules"]
    ids = reference.splits["test"]
    texts = [reference.dataset.by_id[row].text for row in ids]
    methods = {}
    for name, bundle in bundles.items():
        classifier = load_trusted_local_classifier(
            bundle.root,
            bundle.manifest_sha256,
            trusted_local_artifact=trusted_local_artifacts,
        )
        actual = [
            {"row_id": row, "predicted_label": label}
            for row, label in zip(ids, predict_documents(classifier, texts), strict=True)
        ]
        if actual != bundle.predictions:
            raise ValueError("saved baseline predictions differ from restored model")
        methods[name] = classification_metrics(bundle.dataset, ids, actual)
    predicted = predict_local_encoder(
        encoder,
        texts,
        expected_manifest_sha256=encoder_manifest_sha256,
    )
    records = [
        {"row_id": row, "predicted_label": label} for row, label in zip(ids, predicted, strict=True)
    ]
    methods["encoder"] = classification_metrics(reference.dataset, ids, records)
    return {
        "schema_version": 1,
        "evidence_kind": manifest["evidence_kind"],
        "pretrained_quality": "NOT_RUN"
        if manifest["evidence_kind"] == "teacher-random"
        else "REQUIRES_REVIEW",
        "dataset_sha256": manifest["dataset_sha256"],
        "split_sha256": manifest["split_sha256"],
        "evaluation_ids": list(ids),
        "labels": list(reference.dataset.labels),
        "methods": methods,
        "encoder_predictions": records,
        "bundles": {name: bundle.manifest_sha256 for name, bundle in bundles.items()},
        "encoder_manifest_sha256": encoder_manifest_sha256,
        "environment": {
            "python": platform.python_version(),
            "torch": version("torch"),
            "transformers": version("transformers"),
        },
    }
