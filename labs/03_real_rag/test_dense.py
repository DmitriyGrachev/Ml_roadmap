"""Numeric/index boundary tests; real Qdrant is never imitated as integration."""

import hashlib
import json
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
import pytest

dense = import_module("labs.03_real_rag.dense")


@pytest.mark.parametrize(
    "vectors",
    [
        [[0.0, 0.0]],
        [[float("nan"), 1.0]],
        [[1.0]],
        [],
        [[True, False]],
        [["3", "4"]],
        None,
        {"vector": [1, 0]},
    ],
)
def test_vector_boundary_rejects_invalid_embeddings(vectors: object) -> None:
    with pytest.raises(ValueError, match="vectors"):
        dense.checked_vectors(vectors, rows=1, dimension=2)


def test_vector_boundary_normalizes_without_changing_directions() -> None:
    result = dense.checked_vectors([[3.0, 4.0]], rows=1, dimension=2)
    np.testing.assert_allclose(result, [[0.6, 0.8]])


def test_model_preflight_rejects_missing_local_assets(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="artifact"):
        dense.verified_minilm_identity(tmp_path)


def _pin_unit_model(directory: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Test inventory hashes real local fixture bytes, never claims pretrained assets."""
    model = {
        "id": "UNIT_FIXTURE_NOT_PRETRAINED",
        "revision": "unit-only",
        "files": [
            {
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(directory.iterdir())
        ],
    }
    downloader = import_module("labs.02_huggingface_models.download")
    monkeypatch.setattr(downloader, "resource_manifest", lambda: {"model": model})
    return model


@pytest.mark.parametrize(
    "extra",
    [
        "added_tokens.json",
        "adapter_config.json",
        "nested/tokenizer.json",
        "nested/added_tokens.json",
    ],
)
def test_model_preflight_rejects_every_unlisted_loader_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, extra: str
) -> None:
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tokenizer.json").write_text("{}", encoding="utf-8")
    _pin_unit_model(tmp_path, monkeypatch)
    destination = tmp_path / extra
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text('{"scanner": 91}', encoding="utf-8")
    with pytest.raises(ValueError, match="inventory"):
        dense.verified_minilm_identity(tmp_path)


def test_model_preflight_accepts_exact_verified_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tokenizer.json").write_text("{}", encoding="utf-8")
    expected = _pin_unit_model(tmp_path, monkeypatch)
    identity = dense.verified_minilm_identity(tmp_path)
    assert identity["files"] == expected["files"]


def test_preflight_blocks_added_tokens_with_real_local_tokenizer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    transformers = pytest.importorskip(
        "transformers", reason="NOT_RUN: optional installed tokenizer mechanics"
    )
    tokenizer = transformers.BertTokenizer(
        vocab={"[PAD]": 0, "[UNK]": 1, "[CLS]": 2, "[SEP]": 3, "[MASK]": 4, "scanner": 5}
    )
    tokenizer.save_pretrained(tmp_path)
    _pin_unit_model(tmp_path, monkeypatch)
    dense.verified_minilm_identity(tmp_path)
    # These bytes are a loader-consumed input even when original tokenizer files stay unchanged.
    (tmp_path / "added_tokens.json").write_text('{"scannerunit": 6}', encoding="utf-8")
    with pytest.raises(ValueError, match="inventory"):
        dense.encode_local_minilm(tmp_path, ("scannerunit",))


def test_snapshot_binds_exact_corpus_vector_and_embedding_bytes(tmp_path: Path) -> None:
    demo = import_module("labs.03_real_rag.demo")
    sources = demo.teacher_sources()[:1]
    identity = {"model": "unit numeric fixture", "dimension": 2, "pooling": "hand-vectors"}
    output = tmp_path / "snapshot"
    expected = dense.write_snapshot(output, sources, [[3.0, 4.0]], identity)
    restored = dense.load_snapshot(output, expected)
    assert restored["chunks"][0]["chunk_id"] == "A-SCAN@1:p1"
    assert restored["embedding"]["pooling"] == "hand-vectors"
    (output / "vectors.json").write_text("[[0, 1]]", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact"):
        dense.load_snapshot(output, expected)


def test_snapshot_manifest_must_match_operator_digest(tmp_path: Path) -> None:
    demo = import_module("labs.03_real_rag.demo")
    output = tmp_path / "snapshot"
    expected = dense.write_snapshot(
        output, demo.teacher_sources()[:1], [[1.0, 0.0]], {"dimension": 2, "model": "test"}
    )
    (output / "manifest.json").write_text("{}", encoding="utf-8")
    assert expected != hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="manifest"):
        dense.load_snapshot(output, expected)


def test_snapshot_refuses_reuse(tmp_path: Path) -> None:
    demo = import_module("labs.03_real_rag.demo")
    output = tmp_path / "snapshot"
    output.mkdir()
    with pytest.raises(FileExistsError):
        dense.write_snapshot(
            output, demo.teacher_sources()[:1], [[1.0, 0.0]], {"dimension": 2, "model": "test"}
        )


def test_missing_qdrant_fails_explicitly_without_writing_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = dense.import_module

    def no_qdrant(name: str) -> object:
        if name == "qdrant_client":
            raise ImportError("unit dependency gate")
        return original(name)

    monkeypatch.setattr(dense, "import_module", no_qdrant)
    with pytest.raises(RuntimeError, match="NOT_RUN"):
        dense.qdrant_smoke(tmp_path / "not-created", tmp_path, "0" * 64)
    assert not (tmp_path / "not-created").exists()


def test_real_optional_encoder_is_local_only_before_any_load(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="artifact"):
        dense.encode_local_minilm(tmp_path, ("scanner settings",))


def test_random_encoder_demonstrates_shapes_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("torch", reason="NOT_RUN: optional training environment")
    pytest.importorskip("transformers", reason="NOT_RUN: optional training environment")
    import socket

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("local random encoder attempted network")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    result = dense.random_encoder_mechanics()
    assert result["hidden_shape"] == [2, 5, 16]
    assert result["vectors_shape"] == [2, 16]
    np.testing.assert_allclose(result["row_norms"], [1.0, 1.0])
    assert result["pretrained_quality"] == "NOT_RUN"


def test_two_rankings_keep_private_nearest_vector_out_before_cutoff() -> None:
    demo = import_module("labs.03_real_rag.demo")
    sources = demo.teacher_sources()
    # Deliberately hand-authored geometry, never called real encoder evidence.
    matrix = [[0.9, 0.1], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]]
    report = dense.comparison_trace(sources, matrix, [[1.0, 0.0]] * 5, k=1)
    assert report["q-exact"]["dense"]["chunk_ids"] == ["A-SCAN@1:p1"]
    assert report["q-exact"]["lexical"]["chunk_ids"] == ["A-SCAN@1:p1"]
    assert report["q-paraphrase"]["lexical"]["recall_at_k"] == 0.0
    assert report["q-paraphrase"]["dense"]["recall_at_k"] == 1.0
    # Nonempty dense output on an absent query is not evidence of answerability.
    assert report["q-absent"]["dense"]["recall_at_k"] is None
    assert report["q-absent"]["dense"]["chunk_ids"]


@pytest.mark.parametrize("schema", [True, 1.0, "1", None])
def test_dense_rejects_wrong_schema_scalar(tmp_path: Path, schema: object) -> None:
    demo = import_module("labs.03_real_rag.demo")
    output = tmp_path / "snapshot"
    dense.write_snapshot(
        output, demo.teacher_sources()[:1], [[1.0, 0.0]], {"dimension": 2, "model": "test"}
    )
    path = output / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = schema
    path.write_text(json.dumps(manifest), encoding="utf-8")
    new_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="manifest"):
        dense.load_snapshot(output, new_digest)


def test_hand_snapshot_cli_creates_pinned_geometry_without_encoder(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    snapshot = tmp_path / "hand"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "labs.03_real_rag.dense",
            "hand-snapshot",
            "--output",
            str(snapshot),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(completed.stdout)
    restored = dense.load_snapshot(snapshot, receipt["snapshot_sha256"])
    assert restored["embedding"]["evidence"] == "HAND_AUTHORED_API_GEOMETRY_NOT_EMBEDDINGS"
    assert restored["embedding"]["dimension"] == 2
    np.testing.assert_allclose(restored["vectors"][2], [1.0, 0.0])
    assert receipt["pretrained_quality"] == "NOT_RUN"


def test_snapshot_rejects_declared_dimension_even_with_repinned_manifest(tmp_path: Path) -> None:
    demo = import_module("labs.03_real_rag.demo")
    snapshot = tmp_path / "snapshot"
    dense.write_snapshot(
        snapshot, demo.teacher_sources()[:1], [[1.0, 0.0]], {"dimension": 2, "model": "test"}
    )
    path = snapshot / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["embedding"]["dimension"] = 3
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="shape"):
        dense.load_snapshot(snapshot, hashlib.sha256(path.read_bytes()).hexdigest())
