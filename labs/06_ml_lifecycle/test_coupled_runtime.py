"""Real local Qdrant recovery, gated explicitly; tiny fixture is not model evidence."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import pytest

from projects.document_intelligence_lab.artifacts import file_sha256, json_bytes

from .test_coupled import api, build
from .test_coupled import inputs as inputs
from .test_coupled import only_eventloop_network as only_eventloop_network
from .test_coupled import teacher as teacher

pytestmark = [
    pytest.mark.optional_live,
    pytest.mark.skipif(
        os.environ.get("ROADMAP_RUN_QDRANT") != "1",
        reason="NOT_RUN: explicit local Qdrant gate required",
    ),
]


def prepared(case: dict[str, Any], tmp_path: Path) -> tuple[Path, Path, str]:
    importlib.import_module("qdrant_client")  # Explicit gate makes missing dependency FAIL.
    manifest = build(case, tmp_path / "release")
    return manifest.parent, tmp_path / "storage", file_sha256(manifest)


def test_reconstructs_original_inventory_acl_and_fresh_process(
    inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    recovered, storage, pin = prepared(inputs, tmp_path)
    receipt = api().restore_index_new(recovered, storage, expected_release_sha256=pin)
    assert receipt["point_count"] == 4
    assert receipt["public_top1"][0]["chunk_id"] == "A-SCAN@1:p1"
    assert receipt["generation"] == "NOT_RUN"
    script = """
import importlib,json,runpy,sys
resource=json.loads(sys.argv.pop(1))
importlib.import_module('labs.02_huggingface_models.download').resource_manifest=lambda:{'model':resource}
sys.argv[0]='coupled'
runpy.run_module('labs.06_ml_lifecycle.coupled',run_name='__main__')
"""
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            json_bytes(inputs["resource"]).decode(),
            "verify-index",
            "--root",
            str(recovered),
            "--storage",
            str(storage),
            "--release-sha256",
            pin,
            "--receipt",
            str(tmp_path / "fresh.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    fresh = json.loads(completed.stdout)
    assert fresh["process_id"] != os.getpid()
    assert fresh["point_count"] == 4
    assert fresh["public_top1"][0]["chunk_id"] == "A-SCAN@1:p1"
    assert json.loads((tmp_path / "fresh.json").read_text()) == fresh
    with pytest.raises(FileExistsError):
        api().restore_index_new(recovered, storage, expected_release_sha256=pin)


@pytest.mark.parametrize("mutation", ["missing", "extra", "payload", "vector", "metadata"])
def test_actual_persisted_mutation_is_rejected(
    inputs: dict[str, Any],
    tmp_path: Path,
    mutation: str,
) -> None:
    recovered, storage, pin = prepared(inputs, tmp_path)
    api().restore_index_new(recovered, storage, expected_release_sha256=pin)
    qdrant = importlib.import_module("qdrant_client")
    client = qdrant.QdrantClient(path=str(storage))
    point_id = str(uuid5(NAMESPACE_URL, "A-SCAN@1:p1"))
    try:
        if mutation == "missing":
            client.delete("coupled_author", points_selector=[point_id], wait=True)
        elif mutation == "extra":
            client.upsert(
                "coupled_author",
                points=[
                    qdrant.models.PointStruct(
                        id=str(uuid5(NAMESPACE_URL, "STALE@old:p1")),
                        vector=[1.0, 0.0] + [0.0] * 382,
                        payload={"chunk_id": "STALE@old:p1", "access": "public"},
                    )
                ],
                wait=True,
            )
        elif mutation == "payload":
            client.set_payload("coupled_author", payload={"access": "staff"}, points=[point_id])
        elif mutation == "vector":
            client.update_vectors(
                "coupled_author",
                points=[qdrant.models.PointVectors(id=point_id, vector=[0.0, 1.0] + [0.0] * 382)],
                wait=True,
            )
        else:
            client.update_collection("coupled_author", metadata={"release_sha256": "0" * 64})
    finally:
        client.close()
    with pytest.raises(
        RuntimeError,
        match={
            "missing": "inventory",
            "extra": "inventory",
            "payload": "payload",
            "vector": "vector",
            "metadata": "identity",
        }[mutation],
    ):
        api().verify_index(recovered, storage, expected_release_sha256=pin)


@pytest.mark.parametrize(("distance", "dimension"), [("Dot", 384), ("Cosine", 3)])
def test_actual_wrong_config_is_rejected(
    inputs: dict[str, Any],
    tmp_path: Path,
    distance: str,
    dimension: int,
) -> None:
    recovered, storage, pin = prepared(inputs, tmp_path)
    qdrant = importlib.import_module("qdrant_client")
    client = qdrant.QdrantClient(path=str(storage))
    try:
        client.create_collection(
            "coupled_author",
            vectors_config=qdrant.models.VectorParams(size=dimension, distance=distance),
        )
    finally:
        client.close()
    with pytest.raises(RuntimeError, match="dimension/distance"):
        api().verify_index(recovered, storage, expected_release_sha256=pin)


def test_invalid_release_never_creates_storage(inputs: dict[str, Any], tmp_path: Path) -> None:
    recovered, storage, _ = prepared(inputs, tmp_path)
    with pytest.raises(ValueError, match="sha256"):
        api().restore_index_new(recovered, storage, expected_release_sha256="0" * 64)
    assert not storage.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction boundary")
@pytest.mark.parametrize("entry", ["collection", "nested-junction", "sqlite", "lock"])
def test_existing_storage_link_is_rejected_before_client_open(
    inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
) -> None:
    recovered, storage, pin = prepared(inputs, tmp_path)
    api().restore_index_new(recovered, storage, expected_release_sha256=pin)
    if entry == "nested-junction":
        destination = tmp_path / "external-directory"
        destination.mkdir()
        linked = storage / "collection/unrelated"
    else:
        linked = {
            "collection": storage / "collection/coupled_author",
            "sqlite": storage / "collection/coupled_author/storage.sqlite",
            "lock": storage / ".lock",
        }[entry]
        assert linked.exists(), "real Qdrant runtime must create the targeted storage entry"
        destination = tmp_path / ("external-" + linked.name)
        linked.rename(destination)
    if entry in {"collection", "nested-junction"}:
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(linked), str(destination)],
            check=True,
            capture_output=True,
            text=True,
        )
        assert linked.is_junction()
    else:
        try:
            linked.symlink_to(destination)
        except OSError as exc:
            pytest.skip(f"Windows file symlink privilege unavailable: {exc}")
        assert linked.is_symlink()
    qdrant = importlib.import_module("qdrant_client")

    def forbid_client_open(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Qdrant client opened before rejecting linked storage")

    # The real runtime built the store. Only the final open boundary is blocked:
    # a rejected path must never reach Qdrant/SQLite, even if it contains valid bytes.
    monkeypatch.setattr(qdrant, "QdrantClient", forbid_client_open)
    with pytest.raises(ValueError, match="link"):
        api().verify_index(recovered, storage, expected_release_sha256=pin)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO boundary")
def test_existing_storage_nonregular_entry_is_rejected_before_client_open(
    inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recovered, storage, pin = prepared(inputs, tmp_path)
    api().restore_index_new(recovered, storage, expected_release_sha256=pin)
    make_fifo = getattr(os, "mkfifo", None)
    assert make_fifo is not None, "gated test requires POSIX FIFO support"
    make_fifo(storage / "unexpected-fifo")
    qdrant = importlib.import_module("qdrant_client")

    def forbid_client_open(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Qdrant client opened before rejecting nonregular storage")

    monkeypatch.setattr(qdrant, "QdrantClient", forbid_client_open)
    with pytest.raises(ValueError, match="regular"):
        api().verify_index(recovered, storage, expected_release_sha256=pin)
