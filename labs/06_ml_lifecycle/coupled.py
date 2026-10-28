"""Pinned local classification + retrieval teaching suite; generation is never implicit.

Protect operator-selected directories from concurrent replacement. Checksums bind
bytes, not trust or provenance of how vectors were produced. This is a local disk
and in-process ASGI recovery experiment, not an atomic deployment or server test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
from datetime import UTC, datetime
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import numpy as np

from projects.document_intelligence_lab.artifacts import (
    file_sha256,
    json_bytes,
    read_json,
    verify_bundle,
)
from roadmap_tools.experiment_evidence import checked_artifact

from . import releases

dense = import_module("labs.03_real_rag.dense")
MANIFEST = "coupled-release.json"
COLLECTION = "coupled_author"


def _no_links(path: Path) -> None:
    """Check the lexical path and every ancestor before resolving or traversing it."""
    absolute = path.absolute()
    if any(item.is_symlink() or item.is_junction() for item in (absolute, *absolute.parents)):
        raise ValueError("artifact paths cannot contain symlinks or junction links")


def _regular_tree(root: Path) -> tuple[set[str], set[str]]:
    """Inspect every entry without traversing links before any artifact/runtime open."""
    _no_links(root)
    if not root.is_dir():
        raise ValueError("artifact inventory requires a directory")
    files: set[str] = set()
    directories: set[str] = set()
    pending = [root]
    while pending:
        directory = pending.pop()
        for item in directory.iterdir():
            _no_links(item)
            relative = item.relative_to(root).as_posix()
            if item.is_dir():
                directories.add(relative)
                pending.append(item)
            elif item.is_file():
                files.add(relative)
            else:
                raise ValueError("artifact inventory requires regular files")
    return files, directories


def _inventory(root: Path, expected: set[str], optional: set[str] | None = None) -> None:
    files, directories = _regular_tree(root)
    allowed = expected | (optional or set())
    parents = {
        parent.as_posix()
        for name in allowed
        for parent in Path(name).parents
        if parent != Path(".")
    }
    if not expected <= files or not files <= allowed or not directories <= parents:
        raise ValueError("artifact inventory differs from verified files")


def _new(path: Path) -> None:
    _no_links(path)
    if path.exists():
        raise FileExistsError(f"new output required: {path}")


def _outside_inputs(output: Path, *roots: Path) -> None:
    for root in roots:
        _no_links(root)
        if output.resolve().is_relative_to(root.resolve()):
            raise ValueError("new output must remain outside pinned input artifact directories")


def _copy_files(source: Path, target: Path, names: set[str]) -> None:
    target.mkdir(parents=True, exist_ok=False)
    for name in sorted(names):
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, destination)


def _parts(
    classification: Path,
    snapshot: Path,
    model: Path,
    classification_pin: str,
    snapshot_pin: str,
    *,
    allow_snapshot_observations: bool = False,
) -> dict[str, Any]:
    for root in (classification, snapshot, model):
        _no_links(root)
        # Reject links before existing helpers resolve file paths.
        if root.is_dir():
            pending = [root]
            while pending:
                for item in pending.pop().iterdir():
                    _no_links(item)
                    if item.is_dir():
                        pending.append(item)
    classified = releases.verify_release(classification, expected_release_sha256=classification_pin)
    bundle = verify_bundle(
        classification / "bundle", expected_manifest_sha256=classified["bundle_sha256"]
    )
    classification_files = {"release.json", "bundle/manifest.json"} | {
        "bundle/" + path.relative_to(bundle.root).as_posix() for path in bundle.paths.values()
    }
    _inventory(classification, classification_files, {"restart.json"})
    snapshot_files = {"manifest.json", "sources.json", "chunks.json", "vectors.json"}
    _inventory(
        snapshot,
        snapshot_files,
        {"retrieval-comparison.json", "query-evidence.json"}
        if allow_snapshot_observations
        else None,
    )
    data = dense.load_snapshot(snapshot, snapshot_pin)
    identity = dense.verified_minilm_identity(model)
    model_files = {entry["filename"] for entry in identity["files"]}
    if len(model_files) != 6:
        raise ValueError("coupled model requires the full exact six-file inventory")
    _inventory(model, model_files)
    if json_bytes(data["embedding"]) != json_bytes(identity):
        raise ValueError("snapshot representation differs from verified model identity")
    if not any(chunk["access"] == "public" for chunk in data["chunks"]):
        raise ValueError("coupled parity probe requires a public chunk")
    return {
        "classification": classified,
        "data": data,
        "embedding": identity,
        "classification_files": classification_files,
        "snapshot_files": snapshot_files,
        "model_files": model_files,
    }


def _code() -> dict[str, Any]:
    return {
        "sources_sha256": {
            "coupled": file_sha256(Path(__file__)),
            "classification_releases": file_sha256(Path(str(releases.__file__))),
            "dense_snapshot": file_sha256(Path(str(dense.__file__))),
        },
        "versions": {"python": platform.python_version(), "numpy": version("numpy")},
    }


def _manifest(parts: dict[str, Any], classification_pin: str, snapshot_pin: str) -> dict[str, Any]:
    data = parts["data"]
    point_ids = [str(uuid5(NAMESPACE_URL, chunk["chunk_id"])) for chunk in data["chunks"]]
    return {
        "schema_version": 1,
        "evidence_kind": "AUTHOR_COUPLED_LOCAL_RECOVERY_SUITE_ONLY",
        "selection_scope": (
            "two jointly selected teaching branches; classifier data is not RAG corpus"
        ),
        "classification": {
            "path": "classification",
            "release_sha256": classification_pin,
            "identity": parts["classification"]["identity"],
        },
        "snapshot": {"path": "snapshot", "manifest_sha256": snapshot_pin},
        "model": {"path": "model", "identity": parts["embedding"]},
        "embedding": parts["embedding"],
        "corpus": {
            "sources_sha256": data["artifacts"]["sources.json"]["sha256"],
            "chunks_sha256": data["artifacts"]["chunks.json"]["sha256"],
            "vectors_sha256": data["artifacts"]["vectors.json"]["sha256"],
            "normalization": dense.rag.NORMALIZATION,
            "chunking": dense.rag.CHUNK_POLICY,
        },
        "index": {
            "engine": "qdrant-local",
            "collection": COLLECTION,
            "point_id_policy": "UUID5(NAMESPACE_URL,chunk_id)",
            "point_ids": point_ids,
            "dimension": parts["embedding"]["dimension"],
            "distance": "Cosine",
            "vectors": "single-unnamed-dense-l2-v1",
            "payload": "exact-snapshot-chunk-v1",
            "acl_before_top_k": "public",
            "probe": "first-public-chunk-self-query-parity-only",
        },
        "code": _code(),
        "generator": None,
    }


def write_coupled_release_new(
    classification_release: Path,
    snapshot: Path,
    model_dir: Path,
    output: Path,
    *,
    expected_classification_release_sha256: str,
    expected_snapshot_sha256: str,
) -> Path:
    """Verify all inputs before creating NEW output; copy only verified regular bytes."""
    _new(output)
    _outside_inputs(output, classification_release, snapshot, model_dir)
    parts = _parts(
        classification_release,
        snapshot,
        model_dir,
        expected_classification_release_sha256,
        expected_snapshot_sha256,
        allow_snapshot_observations=True,
    )
    manifest = _manifest(parts, expected_classification_release_sha256, expected_snapshot_sha256)
    output.mkdir(parents=True, exist_ok=False)
    for source, name in (
        (classification_release, "classification"),
        (snapshot, "snapshot"),
        (model_dir, "model"),
    ):
        _copy_files(source, output / name, parts[name + "_files"])
    path = output / MANIFEST
    path.write_bytes(json_bytes(manifest))
    verify_coupled_release(output, expected_release_sha256=file_sha256(path))
    return path


def verify_coupled_release(root: Path, *, expected_release_sha256: str) -> dict[str, Any]:
    """Offline integrity/compatibility only: no pickle, torch, encoder or Qdrant."""
    _no_links(root)
    _no_links(root / MANIFEST)
    path = checked_artifact(root, MANIFEST, expected_release_sha256)
    manifest = read_json(path)
    try:
        classification_pin = manifest["classification"]["release_sha256"]
        snapshot_pin = manifest["snapshot"]["manifest_sha256"]
    except (KeyError, TypeError) as exc:
        raise ValueError("invalid coupled identity schema") from exc
    parts = _parts(
        root / "classification", root / "snapshot", root / "model", classification_pin, snapshot_pin
    )
    expected = _manifest(parts, classification_pin, snapshot_pin)
    if type(manifest.get("schema_version")) is not int or json_bytes(manifest) != json_bytes(
        expected
    ):
        raise ValueError("coupled identity/config/code differs from verified bytes")
    files = {MANIFEST} | {
        name + "/" + filename
        for name in ("classification", "snapshot", "model")
        for filename in parts[name + "_files"]
    }
    _inventory(root, files, {"recovery.json", "classification/restart.json"})
    return cast(dict[str, Any], manifest)


def _receipt(kind: str, pin: str, started: float) -> dict[str, Any]:
    return {
        "evidence_kind": kind,
        "release_sha256": pin,
        "process_id": os.getpid(),
        "created_utc": datetime.now(UTC).isoformat(),
        "versions": {"python": platform.python_version(), "numpy": version("numpy")},
        "elapsed_seconds": perf_counter() - started,
        "generation": "NOT_RUN",
        "vllm": "DEFERRED_ENV",
        "network_server": "NOT_RUN",
        "timing_scope": "single local recovery/check wall time; not a latency benchmark",
    }


def restore_coupled_release_new(
    root: Path,
    output: Path,
    *,
    expected_release_sha256: str,
    trusted_local_artifact: bool = False,
) -> Path:
    """Recover into NEW storage and actually check ASGI readiness/inference.

    Qdrant recovery is a separate explicit command/process in its prepared runtime.
    Partial runtime failures retain output for operator inspection; never reuse it.
    """
    started = perf_counter()
    _new(output)
    _outside_inputs(output, root)
    manifest = verify_coupled_release(root, expected_release_sha256=expected_release_sha256)
    nested_pin = manifest["classification"]["release_sha256"]
    bundle = verify_bundle(
        root / "classification/bundle",
        expected_manifest_sha256=releases.verify_release(
            root / "classification", expected_release_sha256=nested_pin
        )["bundle_sha256"],
    )
    if bundle.manifest["model"]["format"] != "rules-json-v1" and trusted_local_artifact is not True:
        raise ValueError("pickle requires an explicitly trusted local artifact")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(root / MANIFEST, output / MANIFEST)
    for name in ("snapshot", "model"):
        names = (
            {"manifest.json", "sources.json", "chunks.json", "vectors.json"}
            if name == "snapshot"
            else {entry["filename"] for entry in manifest["embedding"]["files"]}
        )
        _copy_files(root / name, output / name, names)
    releases.restore_release_new(
        root / "classification",
        output / "classification",
        expected_release_sha256=nested_pin,
        trusted_local_artifact=trusted_local_artifact,
    )
    verify_coupled_release(output, expected_release_sha256=expected_release_sha256)
    receipt = _receipt("AUTHOR_COUPLED_ASGI_RECOVERY_ONLY", expected_release_sha256, started)
    receipt.update(
        {
            "classification_release_sha256": nested_pin,
            "snapshot_sha256": manifest["snapshot"]["manifest_sha256"],
            "ready": True,
            "index": "NOT_RUN_SEPARATE_RAG_PROCESS_REQUIRED",
            "restart": read_json(output / "classification/restart.json"),
        }
    )
    (output / "recovery.json").write_bytes(json_bytes(receipt))
    return output


def _qdrant() -> Any:
    try:
        return import_module("qdrant_client")
    except ImportError as exc:
        raise RuntimeError("Qdrant NOT_RUN: use the prepared retrieval environment") from exc


def _binding(manifest: dict[str, Any], pin: str) -> dict[str, Any]:
    return {
        "release_sha256": pin,
        "snapshot_sha256": manifest["snapshot"]["manifest_sha256"],
        "embedding": manifest["embedding"],
        "index": manifest["index"],
    }


def restore_index_new(
    recovered: Path, storage: Path, *, expected_release_sha256: str
) -> dict[str, Any]:
    """Reconstruct exact original snapshot points, never the old smoke mutation plan."""
    started = perf_counter()
    _new(storage)
    _outside_inputs(storage, recovered)
    manifest = verify_coupled_release(recovered, expected_release_sha256=expected_release_sha256)
    data = dense.load_snapshot(recovered / "snapshot", manifest["snapshot"]["manifest_sha256"])
    qdrant = _qdrant()
    storage.mkdir(parents=True, exist_ok=False)
    client = qdrant.QdrantClient(path=str(storage.resolve()))
    try:
        client.create_collection(
            COLLECTION,
            vectors_config=qdrant.models.VectorParams(
                size=manifest["embedding"]["dimension"], distance=qdrant.models.Distance.COSINE
            ),
            metadata=_binding(manifest, expected_release_sha256),
        )
        client.upsert(
            COLLECTION,
            points=[
                qdrant.models.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, chunk["chunk_id"])),
                    payload=chunk,
                    vector=vector.tolist(),
                )
                for chunk, vector in zip(data["chunks"], data["vectors"], strict=True)
            ],
            wait=True,
        )
    finally:
        client.close()
    checked = verify_index(recovered, storage, expected_release_sha256=expected_release_sha256)
    checked["evidence_kind"] = "AUTHOR_ACTUAL_LOCAL_COUPLED_INDEX_RECONSTRUCTION"
    checked["elapsed_seconds"] = perf_counter() - started
    return checked


def verify_index(recovered: Path, storage: Path, *, expected_release_sha256: str) -> dict[str, Any]:
    """Reopen and inspect exact config, metadata, IDs, payloads and numeric vectors."""
    started = perf_counter()
    manifest = verify_coupled_release(recovered, expected_release_sha256=expected_release_sha256)
    data = dense.load_snapshot(recovered / "snapshot", manifest["snapshot"]["manifest_sha256"])
    _regular_tree(storage)
    if not (storage / "meta.json").is_file():
        raise ValueError("existing local Qdrant storage required")
    qdrant = _qdrant()
    client = qdrant.QdrantClient(path=str(storage.resolve()))
    try:
        info = client.get_collection(COLLECTION)
        config = info.config.params.vectors
        if (
            not isinstance(config, qdrant.models.VectorParams)
            or config.size != manifest["embedding"]["dimension"]
            or config.distance != qdrant.models.Distance.COSINE
        ):
            raise RuntimeError("actual index dimension/distance mismatch")
        if info.config.metadata != _binding(manifest, expected_release_sha256):
            raise RuntimeError("actual index metadata identity mismatch")
        points, cursor = client.scroll(COLLECTION, limit=1000, with_payload=True, with_vectors=True)
        actual = {str(point.id): point for point in points}
        expected = {
            str(uuid5(NAMESPACE_URL, chunk["chunk_id"])): {
                "payload": chunk,
                "vector": vector.tolist(),
            }
            for chunk, vector in zip(data["chunks"], data["vectors"], strict=True)
        }
        if cursor is not None or set(actual) != set(expected) or len(actual) != len(points):
            raise RuntimeError("actual index persisted inventory mismatch")
        for point_id, entry in expected.items():
            point = actual[point_id]
            if point.payload != entry["payload"]:
                raise RuntimeError("actual index persisted payload mismatch")
            try:
                vector = np.asarray(point.vector)
                matches = (
                    vector.shape == (manifest["embedding"]["dimension"],)
                    and vector.dtype.kind in {"i", "u", "f"}
                    and np.isfinite(vector).all()
                    and np.allclose(vector, entry["vector"], atol=1e-6, rtol=1e-6)
                )
            except (ValueError, TypeError):
                matches = False
            if not matches:
                raise RuntimeError("actual index persisted vector mismatch")
        public_indices = [
            i for i, chunk in enumerate(data["chunks"]) if chunk["access"] == "public"
        ]
        query = data["vectors"][public_indices[0]]
        scores = {
            str(uuid5(NAMESPACE_URL, data["chunks"][i]["chunk_id"])): float(
                data["vectors"][i] @ query
            )
            for i in public_indices
        }
        best = max(scores.values())
        acl = qdrant.models.Filter(
            must=[
                qdrant.models.FieldCondition(
                    key="access", match=qdrant.models.MatchValue(value="public")
                )
            ]
        )
        hits = client.query_points(
            COLLECTION, query=query.tolist(), query_filter=acl, limit=1, with_payload=True
        ).points
        if (
            len(hits) != 1
            or str(hits[0].id) not in scores
            or not np.isclose(scores[str(hits[0].id)], best, atol=1e-6, rtol=1e-6)
            or not np.isclose(hits[0].score, best, atol=1e-6, rtol=1e-6)
        ):
            raise RuntimeError("actual index public ACL before top-k parity mismatch")
        receipt = _receipt(
            "AUTHOR_ACTUAL_LOCAL_COUPLED_INDEX_VERIFICATION", expected_release_sha256, started
        )
        receipt.update(
            {
                "qdrant_client_version": version("qdrant-client"),
                "snapshot_sha256": manifest["snapshot"]["manifest_sha256"],
                "point_count": len(actual),
                "inventory_sha256": hashlib.sha256(json_bytes(expected)).hexdigest(),
                "public_top1": [
                    {
                        "point_id": str(hit.id),
                        "chunk_id": hit.payload["chunk_id"],
                        "score": float(hit.score),
                    }
                    for hit in hits
                ],
                "retrieval_quality": "NOT_MEASURED_SELF_QUERY_PARITY_ONLY",
            }
        )
        return receipt
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("write", "verify", "restore", "index", "verify-index"):
        sub = commands.add_parser(command)
        sub.add_argument("--receipt", required=True, type=Path)
        if command == "write":
            sub.add_argument("--classification-release", required=True, type=Path)
            sub.add_argument("--classification-release-sha256", required=True)
            sub.add_argument("--snapshot", required=True, type=Path)
            sub.add_argument("--snapshot-sha256", required=True)
            sub.add_argument("--model-dir", required=True, type=Path)
            sub.add_argument("--output", required=True, type=Path)
        else:
            sub.add_argument("--root", required=True, type=Path)
            sub.add_argument("--release-sha256", required=True)
            if command == "restore":
                sub.add_argument("--output", required=True, type=Path)
                sub.add_argument("--trusted-local-artifact", action="store_true")
            elif command in {"index", "verify-index"}:
                sub.add_argument("--storage", required=True, type=Path)
    args = parser.parse_args()
    _new(args.receipt)
    protected = [
        getattr(args, name)
        for name in ("root", "classification_release", "snapshot", "model_dir", "output", "storage")
        if hasattr(args, name)
    ]
    for directory in protected:
        _no_links(directory)
        if args.receipt.resolve().is_relative_to(directory.resolve()):
            raise ValueError("receipt must remain outside input and output artifact directories")
    started = perf_counter()
    if args.command == "write":
        path = write_coupled_release_new(
            args.classification_release,
            args.snapshot,
            args.model_dir,
            args.output,
            expected_classification_release_sha256=args.classification_release_sha256,
            expected_snapshot_sha256=args.snapshot_sha256,
        )
        result = _receipt("AUTHOR_COUPLED_WRITE", file_sha256(path), started)
        result["manifest_path"] = str(path)
    elif args.command == "verify":
        verify_coupled_release(args.root, expected_release_sha256=args.release_sha256)
        result = _receipt("AUTHOR_COUPLED_VERIFY", args.release_sha256, started)
    elif args.command == "restore":
        output = restore_coupled_release_new(
            args.root,
            args.output,
            expected_release_sha256=args.release_sha256,
            trusted_local_artifact=args.trusted_local_artifact,
        )
        result = read_json(output / "recovery.json")
    else:
        action = restore_index_new if args.command == "index" else verify_index
        result = action(args.root, args.storage, expected_release_sha256=args.release_sha256)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("xb") as stream:
        stream.write(json_bytes(result))
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
