"""Encoder inventory and cohort boundaries, independent of installed ML packages."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import ModuleType

import pytest


def protocol() -> ModuleType:
    assert Path(__file__).with_name("protocol.py").is_file(), "Encoder adapter is not implemented"
    return importlib.import_module("projects.document_intelligence_lab.part_a.protocol")


def checkpoint(tmp_path: Path) -> Path:
    root = tmp_path / "encoder"
    root.mkdir()
    (root / "config.json").write_text(
        json.dumps({"id2label": {"0": "a", "1": "b"}, "max_position_embeddings": 16}),
        encoding="utf-8",
    )
    (root / "tokenizer.json").write_text("{}", encoding="utf-8")
    (root / "model.safetensors").write_bytes(b"fake bytes: contract test only")
    return root


def register(root: Path, **overrides: object) -> str:
    options: dict[str, object] = {
        "labels": ["a", "b"],
        "dataset_sha256": "1" * 64,
        "split_sha256": "2" * 64,
        "source_revision": "local-config-seed-17",
        "evidence_kind": "teacher-random",
        "batch_size": 2,
        "max_length": 8,
    }
    options.update(overrides)
    return str(protocol().register_checkpoint(root, **options))


def test_inventory_is_bound_to_bytes_and_fixed_data_identity(tmp_path: Path) -> None:
    root = checkpoint(tmp_path)
    digest = register(root)
    value = protocol().verify_checkpoint(root, expected_manifest_sha256=digest)
    assert value["dataset_sha256"] == "1" * 64
    assert value["labels"] == ["a", "b"]
    (root / "model.safetensors").write_bytes(b"replaced")
    with pytest.raises(ValueError, match="sha256"):
        protocol().verify_checkpoint(root, expected_manifest_sha256=digest)


def test_checkpoint_registration_refuses_existing_manifest(tmp_path: Path) -> None:
    root = checkpoint(tmp_path)
    register(root)
    before = (root / "encoder-manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        register(root)
    assert (root / "encoder-manifest.json").read_bytes() == before


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("labels", ["b", "a"]),
        ("batch_size", 0),
        ("batch_size", True),
        ("max_length", 17),
        ("evidence_kind", "quality-verified"),
        ("dataset_sha256", "not-a-digest"),
    ],
)
def test_preflight_rejects_invalid_mapping_limits_or_claims(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    with pytest.raises(ValueError, match=r"mapping|batch_size|max_length|evidence_kind|sha256"):
        register(checkpoint(tmp_path), **{field: value})


def test_uninventoried_file_cannot_change_the_local_loader(tmp_path: Path) -> None:
    root = checkpoint(tmp_path)
    digest = register(root)
    (root / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="inventory"):
        protocol().verify_checkpoint(root, expected_manifest_sha256=digest)


def test_encoder_comparison_rejects_a_different_split_before_inference(tmp_path: Path) -> None:
    a1 = importlib.import_module("projects.document_intelligence_lab.part_a1.demo")
    artifacts = importlib.import_module("projects.document_intelligence_lab.artifacts")
    run = a1.run_demo(tmp_path / "a1")
    rules = run / "rules"
    linear = run / "tfidf-linear"
    refs = {
        name: (path, artifacts.file_sha256(path / "manifest.json"))
        for name, path in (("rules", rules), ("tfidf-linear", linear))
    }
    encoder = checkpoint(tmp_path)
    digest = register(encoder)
    with pytest.raises(ValueError, match=r"cohort|identity"):
        protocol().compare(refs, encoder, encoder_manifest_sha256=digest)


def test_comparison_requires_operator_trust_before_loading_pickle(tmp_path: Path) -> None:
    a1 = importlib.import_module("projects.document_intelligence_lab.part_a1.demo")
    artifacts = importlib.import_module("projects.document_intelligence_lab.artifacts")
    run = a1.run_demo(tmp_path / "a1")
    roots = {name: run / name for name in ("rules", "tfidf-linear")}
    reference = artifacts.read_json(roots["rules"] / "manifest.json")
    root = checkpoint(tmp_path)
    config = {"id2label": dict(enumerate(reference["labels"])), "max_position_embeddings": 16}
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    digest = register(
        root,
        labels=reference["labels"],
        dataset_sha256=reference["dataset_sha256"],
        split_sha256=reference["split_sha256"],
    )
    refs = {
        name: (path, artifacts.file_sha256(path / "manifest.json")) for name, path in roots.items()
    }
    with pytest.raises(ValueError, match=r"trust|pickle"):
        protocol().compare(refs, root, encoder_manifest_sha256=digest)
