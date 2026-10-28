"""Dense artifact boundary and opt-in local Qdrant mechanics; no downloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, replace
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import numpy as np
from numpy.typing import NDArray

from roadmap_tools.experiment_evidence import checked_artifact

from .demo import FIXTURES, _checked_entry, _validate_sources, _write_json, rag


def checked_vectors(vectors: Any, *, rows: int, dimension: int) -> NDArray[np.float64]:
    """Validate finite nonzero rows and normalize for the declared cosine contract."""
    if type(dimension) is not int or not 1 <= dimension <= 4096 or not 1 <= rows <= 1000:
        raise ValueError("vectors require bounded row count and dimension")
    try:
        raw = np.asarray(vectors)
        if raw.dtype.kind not in {"i", "u", "f"}:
            raise ValueError("vectors must be numeric, not coerced strings or booleans")
        array = np.asarray(raw, dtype=np.float64)
    except (TypeError, OverflowError) as exc:
        raise ValueError("vectors must be a bounded numeric array") from exc
    if array.shape != (rows, dimension) or not np.isfinite(array).all():
        raise ValueError("vectors must have the declared finite [N, D] shape")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if not np.isfinite(norms).all() or np.any(norms <= 0):
        raise ValueError("vectors must be finite and nonzero")
    return cast(NDArray[np.float64], array / norms)


def random_encoder_mechanics() -> dict[str, Any]:
    """Reuse HF's local random architecture; show CLS shapes, never quality ranks."""
    torch = import_module("torch")
    model, tokenizer = import_module("labs.02_huggingface_models.example").make_local_components()
    tokens = tokenizer(
        ["red", "large blue square"],
        padding=True,
        truncation=True,
        max_length=8,
        return_tensors="pt",
    )
    model.eval()
    with torch.inference_mode():
        hidden = model.bert(**tokens).last_hidden_state
    vectors = checked_vectors(hidden[:, 0].cpu().numpy(), rows=2, dimension=16)
    return {
        "evidence": "LOCAL_RANDOM_ENCODER_SHAPES_ONLY",
        "hidden_shape": list(hidden.shape),
        "vectors_shape": list(vectors.shape),
        "row_norms": np.linalg.norm(vectors, axis=1).tolist(),
        "pooling": "first-token-last-hidden-state-l2-v1",
        "pretrained_quality": "NOT_RUN",
    }


def comparison_trace(
    sources: tuple[Any, ...], document_vectors: Any, query_vectors: Any, *, k: int = 2
) -> dict[str, Any]:
    """One fixed teacher study, not a generalized student ranking-study solution.

    Caller must supply vectors from the SAME declared encoder/preprocessing.
    This function cannot establish their origin; the optional runner binds it.
    Zero-positive judgments have null metrics, not fabricated zero/one quality.
    """
    _validate_sources(sources)
    if type(k) is not int or not 1 <= k <= 10:
        raise ValueError("k must be an integer in 1..10")
    chunks = [chunk for source in sources for chunk in rag.chunks(source)]
    queries = json.loads((FIXTURES / "queries.json").read_text(encoding="utf-8"))["queries"]
    raw = np.asarray(document_vectors)
    dimension = raw.shape[1] if raw.ndim == 2 else 0
    documents = checked_vectors(document_vectors, rows=len(chunks), dimension=dimension)
    questions = checked_vectors(query_vectors, rows=len(queries), dimension=dimension)
    eligible = [index for index, chunk in enumerate(chunks) if chunk.access == "public"]
    report: dict[str, Any] = {}
    for row, query_vector in zip(queries, questions, strict=True):
        dense_ranks = sorted(
            (
                (float(documents[index] @ query_vector), chunks[index].chunk_id)
                for index in eligible
            ),
            key=lambda pair: (-pair[0], pair[1]),
        )[:k]
        lexical = rag.retrieve(row["text"], sources, ("public",), k)
        rankings = {
            "lexical": [(candidate.score, candidate.chunk_id) for candidate in lexical],
            "dense": dense_ranks,
        }
        report[row["query_id"]] = {}
        relevant = set(row["relevant_chunk_ids"])
        for method, ranking in rankings.items():
            ids = [chunk_id for _, chunk_id in ranking]
            first = next((rank for rank, item in enumerate(ids, 1) if item in relevant), None)
            report[row["query_id"]][method] = {
                "chunk_ids": ids,
                "scores": [score for score, _ in ranking],
                "recall_at_k": len(set(ids) & relevant) / len(relevant) if relevant else None,
                "reciprocal_rank": 1 / first if first else (0.0 if relevant else None),
                "answerable_by_annotation": row["answerable"],
            }
    return report


def verified_minilm_identity(directory: Path) -> dict[str, Any]:
    """Require EXACT pinned HF files, not a directory with extra loader inputs."""
    resources = import_module("labs.02_huggingface_models.download").resource_manifest()
    model = resources["model"]
    for spec in model["files"]:
        path = checked_artifact(directory, spec["filename"], spec["sha256"])
        if path.stat().st_size != spec["size_bytes"]:
            raise ValueError("artifact size mismatch")
    expected_names = {spec["filename"] for spec in model["files"]}
    try:
        entries = tuple(directory.iterdir())
        if {path.name for path in entries} != expected_names or any(
            not path.is_file() or path.is_symlink() or path.is_junction() for path in entries
        ):
            raise ValueError("model inventory must contain exactly the pinned regular files")
    except OSError as exc:
        raise ValueError("model inventory is unreadable") from exc
    return {
        "model": model["id"],
        "revision": model["revision"],
        "files": model["files"],
        "inventory_sha256": hashlib.sha256(
            json.dumps(model, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "directory_policy": "exact-pinned-regular-files-no-extras-or-subdirectories-v1",
        "pooling": "first-token-last-hidden-state-l2-v1",
        "dimension": 384,
        "max_length": 128,
        "batch_size": 8,
        "device": "cpu",
        "evidence": "EXPERIMENTAL_CLS_BASELINE_NOT_MODEL_CARD_MEAN_POOLING",
    }


def encode_local_minilm(directory: Path, texts: tuple[str, ...]) -> tuple[Any, dict[str, Any]]:
    """Explicit pretrained CLS baseline, not a solution to masked-mean student work.

    This is deliberately a different representation from MiniLM's recommended
    sentence pooling. Measure it; do not claim model-card semantic quality.
    Assets must already match the original allowlist; nothing is downloaded.
    """
    identity = verified_minilm_identity(directory)
    if (
        not texts
        or len(texts) > 1000
        or any(not text.strip() or len(text) > 10000 for text in texts)
    ):
        raise ValueError("texts must be a bounded nonempty local batch")
    torch = import_module("torch")
    transformers = import_module("transformers")

    tokenizer = transformers.AutoTokenizer.from_pretrained(
        directory.resolve(), local_files_only=True, trust_remote_code=False
    )
    model = transformers.AutoModel.from_pretrained(
        directory.resolve(), local_files_only=True, trust_remote_code=False, use_safetensors=True
    ).eval()
    batches = []
    with torch.inference_mode():
        for start in range(0, len(texts), 8):
            tokens = tokenizer(
                list(texts[start : start + 8]),
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            )
            batches.append(model(**tokens).last_hidden_state[:, 0].cpu().numpy())
    return checked_vectors(np.concatenate(batches), rows=len(texts), dimension=384), identity


def write_snapshot(
    output: Path,
    sources: tuple[Any, ...],
    vectors: Any,
    embedding: dict[str, Any],
) -> str:
    """Freeze corpus, chunks, vectors and representation together; no executable pickle."""
    _validate_sources(sources)
    chunks = [asdict(chunk) for source in sources for chunk in rag.chunks(source)]
    normalized = checked_vectors(vectors, rows=len(chunks), dimension=embedding["dimension"])
    output.mkdir(parents=True, exist_ok=False)
    _write_json(output / "sources.json", [asdict(source) for source in sources])
    _write_json(output / "chunks.json", chunks)
    _write_json(output / "vectors.json", normalized.tolist())
    manifest = {
        "schema_version": 1,
        "embedding": embedding,
        "normalization": rag.NORMALIZATION,
        "chunking": rag.CHUNK_POLICY,
        "distance": "cosine-l2-normalized",
        "artifacts": {
            name: {
                "path": name,
                "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(),
                "size_bytes": (output / name).stat().st_size,
            }
            for name in ("sources.json", "chunks.json", "vectors.json")
        },
    }
    _write_json(output / "manifest.json", manifest)
    return hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest()


def write_hand_snapshot(output: Path) -> str:
    """One fixed no-encoder geometry: private nearest point must lose to public ACL."""
    from .demo import teacher_sources

    return write_snapshot(
        output,
        teacher_sources(),
        [[0.9, 0.1], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]],
        {
            "model": "NO_MODEL_HAND_AUTHORED_TEACHER_GEOMETRY",
            "dimension": 2,
            "pooling": "none",
            "evidence": "HAND_AUTHORED_API_GEOMETRY_NOT_EMBEDDINGS",
            "query_vector": [1.0, 0.0],
            "pretrained_quality": "NOT_RUN",
        },
    )


def load_snapshot(root: Path, expected_manifest_sha256: str) -> dict[str, Any]:
    """Operator pins manifest digest; verify exact bytes and chunk/source correspondence."""
    try:
        manifest_path = checked_artifact(root, "manifest.json", expected_manifest_sha256)
    except ValueError as exc:
        raise ValueError("manifest identity mismatch") from exc
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
        or manifest.get("normalization") != rag.NORMALIZATION
        or manifest.get("chunking") != rag.CHUNK_POLICY
        or manifest.get("distance") != "cosine-l2-normalized"
    ):
        raise ValueError("incompatible manifest preprocessing")
    content: dict[str, Any] = {}
    for name in ("sources.json", "chunks.json", "vectors.json"):
        path = _checked_entry(root, manifest.get("artifacts"), name)
        content[name] = json.loads(path.read_text(encoding="utf-8"))
    try:
        sources = tuple(rag.Source(**row) for row in content["sources.json"])
    except (TypeError, KeyError) as exc:
        raise ValueError("source artifact must contain Source objects") from exc
    _validate_sources(sources)
    expected_chunks = [asdict(chunk) for source in sources for chunk in rag.chunks(source)]
    if content["chunks.json"] != expected_chunks:
        raise ValueError("chunk/source correspondence mismatch")
    embedding = manifest.get("embedding")
    if not isinstance(embedding, dict) or "dimension" not in embedding:
        raise ValueError("manifest requires embedding dimension")
    vectors = checked_vectors(
        content["vectors.json"],
        rows=len(expected_chunks),
        dimension=embedding["dimension"],
    )
    return {
        "sources": sources,
        "chunks": expected_chunks,
        "vectors": vectors,
        "embedding": manifest["embedding"],
        "artifacts": manifest["artifacts"],
    }


def _qdrant_runtime() -> Any:
    try:
        return import_module("qdrant_client")
    except ImportError as exc:
        raise RuntimeError(
            "Qdrant runtime NOT_RUN: prepare the explicit retrieval environment first"
        ) from exc


def _smoke_plan(data: dict[str, Any]) -> dict[str, Any]:
    """Fixed teacher mutations, not a general ingestion/sync implementation."""
    chunks = data["chunks"]
    eligible = [index for index, chunk in enumerate(chunks) if chunk["access"] == "public"]
    if not eligible:
        raise ValueError("smoke requires public chunks")
    first = eligible[0]
    update_index = next(
        (index for index in eligible if chunks[index]["source_id"] != chunks[first]["source_id"]),
        None,
    )
    if update_index is None:
        raise ValueError("smoke requires two distinct public sources")
    source = next(
        item for item in data["sources"] if item.source_id == chunks[update_index]["source_id"]
    )
    updated = replace(
        source,
        revision=source.revision + "-qdrant-update",
        raw_text="Updated teaching schedule: reading room closes at 15:00.",
    )
    replacement = asdict(rag.chunks(updated)[0])
    ids = [str(uuid5(NAMESPACE_URL, chunk["chunk_id"])) for chunk in chunks]
    stale = [
        ids[index] for index, chunk in enumerate(chunks) if chunk["source_id"] == source.source_id
    ]
    new_id = str(uuid5(NAMESPACE_URL, replacement["chunk_id"]))
    expected = {
        point_id: {"payload": chunk, "vector": vector.tolist()}
        for index, (point_id, chunk, vector) in enumerate(
            zip(ids, chunks, data["vectors"], strict=True)
        )
        if index != first and point_id not in stale
    }
    expected[new_id] = {"payload": replacement, "vector": data["vectors"][update_index].tolist()}
    query = checked_vectors(
        [data["embedding"].get("query_vector", data["vectors"][first].tolist())],
        rows=1,
        dimension=data["embedding"]["dimension"],
    )[0].tolist()
    return {
        "first": first,
        "ids": ids,
        "stale": stale,
        "new_id": new_id,
        "replacement": replacement,
        "update_index": update_index,
        "expected": expected,
        "query": query,
    }


def _query_receipts(client: Any, models: Any, query: Any, limit: int, *, public: bool) -> Any:
    acl = models.Filter(
        must=[models.FieldCondition(key="access", match=models.MatchValue(value="public"))]
    )
    hits = client.query_points(
        collection_name="author_smoke",
        query=query,
        query_filter=acl if public else None,
        limit=limit,
        with_payload=True,
    ).points
    # Privileged mechanics trace records IDs/scores only, not staff source text.
    return [
        {"point_id": str(hit.id), "chunk_id": hit.payload["chunk_id"], "score": float(hit.score)}
        for hit in hits
    ]


def qdrant_verify(storage: Path, snapshot: Path, expected_manifest_sha256: str) -> dict[str, Any]:
    """Reopen without mutation; independently derive final inventory from pinned snapshot.

    Run this CLI in a fresh process after qdrant-smoke exits. The receipt itself is
    not a trusted manifest or a substitute for reading persisted points/vectors.
    """
    started = perf_counter()
    qdrant = _qdrant_runtime()
    data = load_snapshot(snapshot, expected_manifest_sha256)
    plan = _smoke_plan(data)
    if not (storage / "meta.json").is_file():
        raise ValueError("existing local Qdrant storage required")
    client = qdrant.QdrantClient(path=str(storage.resolve()))
    try:
        info = client.get_collection("author_smoke")
        config = info.config.params.vectors
        if (
            config.size != data["embedding"]["dimension"]
            or config.distance != qdrant.models.Distance.COSINE
        ):
            raise RuntimeError("actual Qdrant dimension/distance mismatch")
        if info.config.metadata != {
            "snapshot_sha256": expected_manifest_sha256,
            "embedding": data["embedding"],
        }:
            raise RuntimeError("actual Qdrant representation identity mismatch")
        points, cursor = client.scroll(
            "author_smoke",
            limit=1000,
            with_payload=True,
            with_vectors=True,
        )
        actual = {str(point.id): point for point in points}
        if cursor is not None or set(actual) != set(plan["expected"]):
            raise RuntimeError(
                "actual Qdrant persisted inventory mismatch: deleted/stale/missing point"
            )
        for point_id, expected in plan["expected"].items():
            point = actual[point_id]
            if point.payload != expected["payload"]:
                raise RuntimeError("actual Qdrant persisted payload mismatch")
            if not np.allclose(point.vector, expected["vector"], atol=1e-6, rtol=1e-6):
                raise RuntimeError("actual Qdrant persisted vector mismatch")
        public_query = _query_receipts(
            client, qdrant.models, plan["query"], len(data["chunks"]), public=True
        )
        expected_public = {
            point_id
            for point_id, entry in plan["expected"].items()
            if entry["payload"]["access"] == "public"
        }
        if {row["point_id"] for row in public_query} != expected_public:
            raise RuntimeError("actual Qdrant persisted public query mismatch")
        return {
            "evidence": "ACTUAL_LOCAL_QDRANT_PERSISTENCE_CHECK",
            "process_id": os.getpid(),
            "qdrant_client_version": version("qdrant-client"),
            "python_version": sys.version.split()[0],
            "snapshot_sha256": expected_manifest_sha256,
            "point_count": len(actual),
            "public_query": public_query,
            "absent_point_ids": [plan["ids"][plan["first"]], *plan["stale"]],
            "inventory_sha256": hashlib.sha256(
                json.dumps(plan["expected"], sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "pretrained_quality": "NOT_RUN",
            "generator_quality": "NOT_RUN",
            "elapsed_seconds": perf_counter() - started,
            "timing_scope": "one local verification wall time; not retrieval latency benchmark",
        }
    finally:
        client.close()


def qdrant_smoke(storage: Path, snapshot: Path, expected_manifest_sha256: str) -> dict[str, Any]:
    """OPT-IN actual local disk experiment; no server, encoder, or downloader.

    No URL, service, FastEmbed, downloader, remote client, or existing collection.
    Creates new storage, checks ACL before top-k, revokes/deletes one passage,
    replaces another source revision and checks full inventory after close/reopen.
    Numeric vectors prove API/persistence mechanics, never semantic quality.
    """
    started = perf_counter()
    qdrant = _qdrant_runtime()
    QdrantClient, models = qdrant.QdrantClient, qdrant.models
    data = load_snapshot(snapshot, expected_manifest_sha256)
    chunks = data["chunks"]
    plan = _smoke_plan(data)
    storage.mkdir(parents=True, exist_ok=False)
    first, ids = plan["first"], plan["ids"]
    client = QdrantClient(path=str(storage.resolve()))
    try:
        client.create_collection(
            collection_name="author_smoke",
            vectors_config=models.VectorParams(
                size=data["embedding"]["dimension"], distance=models.Distance.COSINE
            ),
            metadata={"snapshot_sha256": expected_manifest_sha256, "embedding": data["embedding"]},
        )
        client.upsert(
            collection_name="author_smoke",
            points=[
                models.PointStruct(id=point_id, vector=vector.tolist(), payload=chunk)
                for point_id, vector, chunk in zip(ids, data["vectors"], chunks, strict=True)
            ],
            wait=True,
        )

        def public_hits() -> Any:
            return _query_receipts(client, models, plan["query"], len(chunks), public=True)

        before = public_hits()
        eligible_ids = {
            ids[index] for index, chunk in enumerate(chunks) if chunk["access"] == "public"
        }
        if {hit["point_id"] for hit in before} != eligible_ids:
            raise RuntimeError("actual Qdrant ACL/query mismatch")
        top1 = _query_receipts(client, models, plan["query"], 1, public=True)
        if not top1 or top1[0] != before[0]:
            raise RuntimeError("actual Qdrant public ACL before top-k mismatch")
        unfiltered = _query_receipts(client, models, plan["query"], 1, public=False)
        client.set_payload(
            collection_name="author_smoke",
            payload={"access": "staff"},
            points=[ids[first]],
            wait=True,
        )
        after_revoke = public_hits()
        if {hit["point_id"] for hit in after_revoke} != eligible_ids - {ids[first]}:
            raise RuntimeError("actual Qdrant ACL revocation failed")
        client.delete(
            collection_name="author_smoke",
            points_selector=models.PointIdsList(points=[ids[first]]),
            wait=True,
        )
        client.upsert(
            collection_name="author_smoke",
            points=[
                models.PointStruct(
                    id=plan["new_id"],
                    vector=data["vectors"][plan["update_index"]].tolist(),
                    payload=plan["replacement"],
                )
            ],
            wait=True,
        )
        client.delete(
            collection_name="author_smoke",
            points_selector=models.PointIdsList(points=plan["stale"]),
            wait=True,
        )
    finally:
        client.close()
    receipt = {
        "evidence": "ACTUAL_LOCAL_QDRANT_MECHANICS_ONLY",
        "process_id": os.getpid(),
        "qdrant_client_version": version("qdrant-client"),
        "python_version": sys.version.split()[0],
        "snapshot_sha256": expected_manifest_sha256,
        "snapshot_artifacts": data["artifacts"],
        "snapshot_manifest_size_bytes": (snapshot / "manifest.json").stat().st_size,
        "embedding": data["embedding"],
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "query_vector": plan["query"],
        "query_before": before,
        "public_top1": top1,
        "unfiltered_top1": unfiltered,
        "query_after_revoke": after_revoke,
        "replacement": plan["replacement"],
        "reopen": qdrant_verify(storage, snapshot, expected_manifest_sha256),
        "pretrained_quality": "NOT_RUN",
        "generator_quality": "NOT_RUN",
    }
    receipt["elapsed_seconds"] = perf_counter() - started
    receipt["timing_scope"] = "one local mutation+reopen wall time; not retrieval latency benchmark"
    _write_json(storage / "mechanics-receipt.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="operation", required=True)
    encoder = subcommands.add_parser("encode-local", help="Explicit existing pretrained asset use")
    encoder.add_argument("--model-dir", required=True, type=Path)
    encoder.add_argument("--output", required=True, type=Path)
    hand = subcommands.add_parser("hand-snapshot", help="No encoder/download; hand API geometry")
    hand.add_argument("--output", required=True, type=Path)
    smoke = subcommands.add_parser("qdrant-smoke", help="Explicit actual local Qdrant; no server")
    smoke.add_argument("--storage", required=True, type=Path)
    smoke.add_argument("--snapshot", required=True, type=Path)
    smoke.add_argument("--manifest-sha256", required=True)
    verify = subcommands.add_parser(
        "qdrant-verify", help="Read persisted experiment in a fresh process"
    )
    verify.add_argument("--storage", required=True, type=Path)
    verify.add_argument("--snapshot", required=True, type=Path)
    verify.add_argument("--manifest-sha256", required=True)
    verify.add_argument("--receipt", type=Path, help="Optional new receipt file; no overwrite")
    subcommands.add_parser("random-mechanics", help="Installed local random HF shape smoke only")
    args = parser.parse_args()
    if args.operation == "hand-snapshot":
        print(
            json.dumps(
                {
                    "snapshot_sha256": write_hand_snapshot(args.output),
                    "evidence": "HAND_AUTHORED_API_GEOMETRY_NOT_EMBEDDINGS",
                    "pretrained_quality": "NOT_RUN",
                }
            )
        )
    elif args.operation == "encode-local":
        from .demo import teacher_sources

        sources = teacher_sources()
        corpus_texts = tuple(chunk.text for source in sources for chunk in rag.chunks(source))
        query_bytes = (FIXTURES / "queries.json").read_bytes()
        queries = json.loads(query_bytes)["queries"]
        texts = (*corpus_texts, *(row["text"] for row in queries))
        vectors, identity = encode_local_minilm(args.model_dir, texts)
        digest = write_snapshot(args.output, sources, vectors[: len(corpus_texts)], identity)
        comparison = comparison_trace(
            sources, vectors[: len(corpus_texts)], vectors[len(corpus_texts) :]
        )
        _write_json(
            args.output / "retrieval-comparison.json",
            {
                "snapshot_sha256": digest,
                "judgments_sha256": hashlib.sha256(query_bytes).hexdigest(),
                "embedding": identity,
                "evidence": "ACTUAL_PRETRAINED_CLS_BASELINE_TEACHER_CASES_ONLY",
                "per_query": comparison,
                "answer_quality": "NOT_RUN",
                "interpretation": "REQUIRES_REVIEW",
            },
        )
        print(json.dumps({"snapshot_sha256": digest, "interpretation": "REQUIRES_REVIEW"}))
    elif args.operation == "random-mechanics":
        print(json.dumps(random_encoder_mechanics()))
    elif args.operation == "qdrant-verify":
        if args.receipt is not None and args.receipt.exists():
            raise FileExistsError(args.receipt)
        receipt = qdrant_verify(args.storage, args.snapshot, args.manifest_sha256)
        if args.receipt is not None:
            _write_json(args.receipt, receipt)
        print(json.dumps(receipt))
    else:
        print(json.dumps(qdrant_smoke(args.storage, args.snapshot, args.manifest_sha256)))


if __name__ == "__main__":
    main()
