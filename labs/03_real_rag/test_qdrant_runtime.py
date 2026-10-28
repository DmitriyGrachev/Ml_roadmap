"""Explicit local-disk Qdrant integration; never enabled by ordinary pytest."""

import json
import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest

pytestmark = [
    pytest.mark.optional_live,
    pytest.mark.skipif(
        os.environ.get("ROADMAP_RUN_QDRANT") != "1",
        reason="NOT_RUN: set ROADMAP_RUN_QDRANT=1 in the prepared retrieval environment",
    ),
]

dense = import_module("labs.03_real_rag.dense")


def _prepared(tmp_path: Path) -> tuple[Path, Path, str]:
    # With the explicit gate, missing runtime is a failure, never a false integration pass.
    import_module("qdrant_client")
    snapshot, storage = tmp_path / "snapshot", tmp_path / "qdrant"
    digest = dense.write_hand_snapshot(snapshot)
    return snapshot, storage, digest


def test_actual_smoke_records_public_topk_update_delete_and_fresh_process(tmp_path: Path) -> None:
    snapshot, storage, digest = _prepared(tmp_path)
    receipt = dense.qdrant_smoke(storage, snapshot, digest)
    assert receipt["query_before"][0]["chunk_id"] == "A-SCAN@1:p1"
    assert receipt["unfiltered_top1"][0]["chunk_id"] == "A-STAFF@1:p1"
    assert {row["chunk_id"] for row in receipt["query_after_revoke"]} == {
        "A-HOURS@1:p1",
        "A-APPENDIX@1:p1",
    }
    assert receipt["reopen"]["point_count"] == 3
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "labs.03_real_rag.dense",
            "qdrant-verify",
            "--storage",
            str(storage),
            "--snapshot",
            str(snapshot),
            "--manifest-sha256",
            digest,
            "--receipt",
            str(storage / "fresh-process-receipt.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    fresh = json.loads(completed.stdout)
    assert fresh["process_id"] != os.getpid()
    assert json.loads((storage / "fresh-process-receipt.json").read_text()) == fresh
    assert fresh["point_count"] == 3
    assert {row["chunk_id"] for row in fresh["public_query"]} == {
        "A-HOURS@1-qdrant-update:p1",
        "A-APPENDIX@1:p1",
    }
    assert fresh["pretrained_quality"] == "NOT_RUN"
    with pytest.raises(FileExistsError):
        dense.qdrant_smoke(storage, snapshot, digest)


@pytest.mark.parametrize("stale_id", ["A-SCAN@1:p1", "A-HOURS@1:p1"])
def test_restart_check_rejects_deleted_or_stale_point_reappearance(
    tmp_path: Path, stale_id: str
) -> None:
    snapshot, storage, digest = _prepared(tmp_path)
    dense.qdrant_smoke(storage, snapshot, digest)
    qdrant = import_module("qdrant_client")
    client = qdrant.QdrantClient(path=str(storage))
    try:
        client.upsert(
            "author_smoke",
            [
                qdrant.models.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, stale_id)),
                    vector=[1.0, 0.0],
                    payload={"chunk_id": stale_id, "access": "public"},
                )
            ],
            wait=True,
        )
    finally:
        client.close()
    with pytest.raises(RuntimeError, match="inventory"):
        dense.qdrant_verify(storage, snapshot, digest)


def test_runtime_rejects_wrong_snapshot_identity_before_storage_creation(tmp_path: Path) -> None:
    snapshot, storage, _ = _prepared(tmp_path)
    with pytest.raises(ValueError, match="manifest"):
        dense.qdrant_smoke(storage, snapshot, "0" * 64)
    assert not storage.exists()


def test_restart_rejects_different_representation_inventory(tmp_path: Path) -> None:
    snapshot, storage, digest = _prepared(tmp_path)
    dense.qdrant_smoke(storage, snapshot, digest)
    demo = import_module("labs.03_real_rag.demo")
    different = tmp_path / "different-identity"
    other_digest = dense.write_snapshot(
        different,
        demo.teacher_sources(),
        [[0.9, 0.1], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]],
        {"dimension": 2, "model": "different inventory", "inventory_sha256": "a" * 64},
    )
    with pytest.raises(RuntimeError, match="identity"):
        dense.qdrant_verify(storage, different, other_digest)


def test_restart_rejects_wrong_persisted_dimension(tmp_path: Path) -> None:
    snapshot, storage, digest = _prepared(tmp_path)
    qdrant = import_module("qdrant_client")
    client = qdrant.QdrantClient(path=str(storage))
    try:
        client.create_collection(
            "author_smoke",
            vectors_config=qdrant.models.VectorParams(
                size=3, distance=qdrant.models.Distance.COSINE
            ),
        )
    finally:
        client.close()
    with pytest.raises(RuntimeError, match="dimension"):
        dense.qdrant_verify(storage, snapshot, digest)
