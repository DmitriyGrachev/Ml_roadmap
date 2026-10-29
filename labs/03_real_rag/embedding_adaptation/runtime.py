"""Explicit bounded local adaptation and read-only evidence contracts."""

import argparse
import hashlib
import json
import math
from importlib import import_module
from pathlib import Path
from time import perf_counter
from typing import Any

MAX_REPORT_BYTES = 10_000_000
REPORT_METADATA_RESERVE_BYTES = 131_072


def _report_bytes(report: dict[str, Any]) -> bytes:
    """Bound encoded UTF-8 before opening a report; this lab is independently runnable."""
    parts = []
    size = 0
    for part in json.JSONEncoder(ensure_ascii=False, allow_nan=False).iterencode(report):
        encoded = part.encode("utf-8")
        size += len(encoded)
        if size > MAX_REPORT_BYTES:
            raise ValueError(f"report byte budget exceeded ({MAX_REPORT_BYTES} UTF-8 bytes)")
        parts.append(encoded)
    return b"".join(parts)


def _write_report(directory: Path, report: dict[str, Any]) -> None:
    payload = _report_bytes(report)
    (directory / "report.json").write_bytes(payload)


def _preflight_report(
    data: dict[str, Any], metadata: dict[str, Any] | None = None, *, k: int = 100
) -> None:
    """Budget both evaluation arms, longest IDs, data and metadata before model work."""
    widest_float = -1.2345678901234567e-123
    longest_ids = sorted(
        (row["id"] for row in data["corpus"]),
        key=lambda doc_id: len(json.dumps(doc_id, ensure_ascii=False).encode("utf-8")),
        reverse=True,
    )[:k]
    results = {
        row["query_id"]: {
            "ids": longest_ids,
            "scores": [widest_float] * len(longest_ids),
            "recall_at_k": widest_float,
            "mrr_at_k": widest_float,
        }
        for row in data["queries"]
        if row["split"] != "train"
    }
    _report_bytes(
        {
            "data": data,
            "train_query_ids": sorted(
                row["query_id"] for row in data["queries"] if row["split"] == "train"
            ),
            # Combining dev/holdout under each arm has the same row payload; reserve
            # covers their fixed wrapper keys and checkpoint metadata not known yet.
            "baseline_and_dev": results,
            "adapted_and_dev": results,
            "known_metadata": metadata or {},
            "reserved_metadata": " " * REPORT_METADATA_RESERVE_BYTES,
        }
    )


def _require(condition: object) -> None:
    if not condition:
        raise ValueError("contract requirement failed")


def validate_data(data: dict[str, Any]) -> None:
    """Reject identity/family leaks before any training; schema intentionally narrow."""
    try:
        corpus, queries = data["corpus"], data["queries"]
        _require(2 <= len(corpus) <= 5000 and 3 <= len(queries) <= 1000)
        ids = [row["id"] for row in corpus]
        _require(len(ids) == len(set(ids)))
        _require(all(isinstance(i, str) and i.strip() for i in ids))
        _require(
            all(isinstance(row["text"], str) and 0 < len(row["text"]) <= 10000 for row in corpus)
        )
        query_ids = [row["query_id"] for row in queries]
        _require(all(isinstance(i, str) and i.strip() for i in query_ids))
        _require(len(query_ids) == len(set(query_ids)))
        _require({row["split"] for row in queries} == {"train", "dev", "holdout"})
        text_splits: dict[str, str] = {}
        family_splits: dict[str, str] = {}
        for row in queries:
            text = " ".join(row["query"].casefold().split())
            family = " ".join(row["family"].casefold().split())
            _require(text and family and len(row["query"]) <= 1000)
            _require(text not in text_splits)
            _require(family not in family_splits or family_splits[family] == row["split"])
            text_splits[text], family_splits[family] = row["split"], row["split"]
            for key in ("positive_ids", "hard_negative_ids"):
                _require(isinstance(row[key], list) and row[key] and len(row[key]) <= 100)
                _require(set(row[key]) <= set(ids))
    except (AssertionError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError("invalid adaptation data or query/family isolation") from exc
    _preflight_report(data)


def validate_submission(directory: Path) -> None:
    """Check saved artifact consistency; the examiner must reproduce model provenance."""
    try:
        report_path = directory / "report.json"
        _require(report_path.stat().st_size <= MAX_REPORT_BYTES)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        _require(report["evidence_kind"] == "LEARNER_LOCAL_PRETRAINED_ADAPTATION")
        _require(report["status"] == "PASS" and report["quality"] == "REQUIRES_REVIEW")
        _require(
            report["learner_source_sha256"]
            == hashlib.sha256(Path(__file__).with_name("starter.py").read_bytes()).hexdigest()
        )
        validate_data(report["data"])
        _require(report["provenance"]["kind"] == "pretrained")
        _require(all(report["provenance"].get(x) for x in ("model_id", "revision", "license")))
        _require(report["baseline_snapshot"] and report["adapted_snapshot"])
        _require(report["baseline_snapshot"] != report["adapted_snapshot"])
        _require(report["adapted_snapshot"] == snapshot(directory / "adapted"))
        _require(report["baseline_weights_sha256"] != report["adapted_weights_sha256"])
        _require(report["reload_weights_equal"] is True)
        _require(type(report["k"]) is int and 1 <= report["k"] <= 100)
        holdout = {r["query_id"] for r in report["data"]["queries"] if r["split"] == "holdout"}
        train = {r["query_id"] for r in report["data"]["queries"] if r["split"] == "train"}
        _require(set(report["train_query_ids"]) == train)
        _require(
            report["objective"] == "cosine_triplet_margin_0.2"
            and type(report["steps"]) is int
            and 1 <= report["steps"] <= 20
        )
        for value in report["timing_seconds"].values():
            _require(type(value) in {int, float} and math.isfinite(value) and value >= 0)
        for mode in ("baseline", "adapted", "dev_baseline", "dev_adapted"):
            results = report[mode]
            expected_queries = (
                {r["query_id"] for r in report["data"]["queries"] if r["split"] == "dev"}
                if mode.startswith("dev_")
                else holdout
            )
            _require(set(results) == expected_queries)
            for qid, row in results.items():
                _require(len(row["ids"]) == len(set(row["ids"])))
                _require(len(row["ids"]) == min(report["k"], len(report["data"]["corpus"])))
                _require(set(row["ids"]) <= {d["id"] for d in report["data"]["corpus"]})
                _require(len(row["scores"]) == len(row["ids"]))
                _require(
                    all(
                        type(score) in {int, float}
                        and math.isfinite(score)
                        and -1.000001 <= score <= 1.000001
                        for score in row["scores"]
                    )
                )
                pairs = list(zip(row["ids"], row["scores"], strict=True))
                _require(pairs == sorted(pairs, key=lambda pair: (-pair[1], pair[0])))
                positives = next(
                    set(q["positive_ids"])
                    for q in report["data"]["queries"]
                    if q["query_id"] == qid
                )
                _require(
                    type(row["recall_at_k"]) in {int, float}
                    and type(row["mrr_at_k"]) in {int, float}
                )
                _require(
                    abs(row["recall_at_k"] - len(positives & set(row["ids"])) / len(positives))
                    < 1e-9
                )
                first = next(
                    (i for i, doc_id in enumerate(row["ids"], 1) if doc_id in positives), None
                )
                _require(abs(row["mrr_at_k"] - (1 / first if first else 0.0)) < 1e-9)
        review = json.loads((directory / "review.json").read_text(encoding="utf-8"))
        _require(review["status"] == "REQUIRES_REVIEW")
        _require(
            all(
                isinstance(review.get(k), str) and len(review[k].strip()) >= 40
                for k in (
                    "hypothesis",
                    "dev_selection",
                    "false_negatives",
                    "failures",
                    "transfer",
                    "provenance_review",
                )
            )
        )
    except (AssertionError, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ValueError(
            "adaptation evidence missing or inconsistent; human review required"
        ) from exc


def snapshot(directory: Path) -> dict[str, str]:
    """Local immutable identities; duplicated here to keep labs independently runnable."""
    files = sorted(p for p in directory.rglob("*") if p.is_file())
    if (
        not directory.is_dir()
        or not files
        or len(files) > 1000
        or sum(p.stat().st_size for p in files) > 2_000_000_000
    ):
        raise ValueError("bounded explicit local snapshot required")
    if any(p.is_symlink() or p.suffix in {".bin", ".pt", ".pth"} for p in files):
        raise ValueError("use safetensors and no symlinks/pickle weights")
    return {
        str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
    }


def _weights(model: Any) -> str:
    digest = hashlib.sha256()
    for name, parameter in model.named_parameters():
        digest.update(name.encode())
        digest.update(parameter.detach().cpu().float().numpy().tobytes())
    return digest.hexdigest()


def retrieve(
    model: Any, corpus: list[dict[str, str]], queries: list[dict[str, Any]], k: int
) -> dict[str, Any]:
    """Actual exact cosine retrieval; identical corpus/query inputs in both arms."""
    started = perf_counter()
    vectors = model.encode(
        [r["text"] for r in corpus],
        normalize_embeddings=True,
        batch_size=8,
        show_progress_bar=False,
    )
    query_vectors = model.encode(
        [r["query"] for r in queries],
        normalize_embeddings=True,
        batch_size=8,
        show_progress_bar=False,
    )
    results = {}
    for query, vector in zip(queries, query_vectors, strict=True):
        scores = vectors @ vector
        if not all(math.isfinite(float(s)) for s in scores):
            raise ValueError("nonfinite encoder scores")
        order = sorted(range(len(corpus)), key=lambda i: (-float(scores[i]), corpus[i]["id"]))[:k]
        ids = [corpus[i]["id"] for i in order]
        positives = set(query["positive_ids"])
        first = next((i for i, doc_id in enumerate(ids, 1) if doc_id in positives), None)
        results[query["query_id"]] = {
            "ids": ids,
            "scores": [float(scores[i]) for i in order],
            "recall_at_k": len(positives & set(ids)) / len(positives),
            "mrr_at_k": 1 / first if first else 0.0,
        }
    return {"results": results, "seconds": perf_counter() - started}


def run_local(
    model_dir: Path,
    data: dict[str, Any],
    output: Path,
    *,
    k: int,
    steps: int,
    seed: int,
    provenance: dict[str, Any],
) -> None:
    """Explicit local pretrained learner experiment; no automatic downloads or tuning."""
    validate_data(data)
    if type(k) is not int or not 1 <= k <= 100 or type(steps) is not int or not 1 <= steps <= 20:
        raise ValueError("k 1..100 and training steps 1..20 required")
    if provenance.get("kind") != "pretrained" or not all(
        provenance.get(x) for x in ("model_id", "revision", "license")
    ):
        raise ValueError("reviewed pretrained model provenance required")
    baseline_snapshot = snapshot(model_dir)
    _preflight_report(
        data,
        {
            "baseline_snapshot": baseline_snapshot,
            "adapted_snapshot": baseline_snapshot,
            "provenance": provenance,
        },
        k=k,
    )
    if not (model_dir / "modules.json").is_file():
        raise ValueError("explicit local SentenceTransformer snapshot with modules.json required")
    try:
        st = import_module("sentence_transformers")
        torch = import_module("torch")
    except ImportError as exc:
        raise RuntimeError("Install optional ranking group: uv sync --group ranking") from exc
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    learner = import_module(__package__ + ".starter")
    partitions = learner.split_queries(data["queries"])
    # Bind the learner's partition output to the validated original rows.
    for split in ("train", "dev", "holdout"):
        if partitions[split] != [r for r in data["queries"] if r["split"] == split]:
            raise ValueError("learner changed partition identity/order")
    triples = learner.make_triples(partitions["train"], data["corpus"])
    if not triples or len(triples) > 10000:
        raise ValueError("bounded nonempty train triples required")
    train_queries = {r["query_id"]: r for r in partitions["train"]}
    if {triple["query_id"] for triple in triples} != set(train_queries):
        raise ValueError("training triples must cover every train query")
    documents = {r["id"]: r["text"] for r in data["corpus"]}
    for triple in triples:
        query = train_queries[triple["query_id"]]
        positive_texts = {" ".join(documents[i].casefold().split()) for i in query["positive_ids"]}
        if not (
            triple["query"] == query["query"]
            and triple["family"] == query["family"]
            and triple["split"] == "train"
            and triple["positive_id"] in query["positive_ids"]
            and triple["negative_id"] in query["hard_negative_ids"]
            and triple["positive"] == documents[triple["positive_id"]]
            and triple["negative"] == documents[triple["negative_id"]]
            and " ".join(triple["negative"].casefold().split()) not in positive_texts
        ):
            raise ValueError("unaligned training triple or known false negative")
    output.mkdir(parents=True, exist_ok=False)
    model = st.SentenceTransformer(
        str(model_dir.resolve()), local_files_only=True, device="cpu", trust_remote_code=False
    )
    model.max_seq_length = min(model.max_seq_length, 128)
    before_weights = _weights(model)
    baseline = retrieve(model, data["corpus"], partitions["holdout"], k)
    dev_baseline = retrieve(model, data["corpus"], partitions["dev"], k)
    started = perf_counter()
    trained = learner.fit_encoder(model, triples, steps=steps, seed=seed)
    if trained is not model or before_weights == _weights(model):
        raise ValueError("learner training did not change actual model weights")
    training_seconds = perf_counter() - started
    model.eval()
    adapted = retrieve(model, data["corpus"], partitions["holdout"], k)
    dev_adapted = retrieve(model, data["corpus"], partitions["dev"], k)
    model.save_pretrained(str(output / "adapted"), safe_serialization=True)
    loaded = st.SentenceTransformer(
        str(output / "adapted"), local_files_only=True, device="cpu", trust_remote_code=False
    )
    if _weights(loaded) != _weights(model):
        raise ValueError("saved checkpoint weight reload mismatch")
    report = {
        "evidence_kind": "LEARNER_LOCAL_PRETRAINED_ADAPTATION",
        "status": "PASS",
        "quality": "REQUIRES_REVIEW",
        "learner_source_sha256": hashlib.sha256(
            Path(__file__).with_name("starter.py").read_bytes()
        ).hexdigest(),
        "provenance": provenance,
        "data": data,
        "k": k,
        "steps": steps,
        "seed": seed,
        "train_query_ids": sorted({r["query_id"] for r in triples}),
        "objective": "cosine_triplet_margin_0.2",
        "baseline_snapshot": baseline_snapshot,
        "adapted_snapshot": snapshot(output / "adapted"),
        "baseline_weights_sha256": before_weights,
        "adapted_weights_sha256": _weights(model),
        "reload_weights_equal": True,
        "baseline": baseline["results"],
        "adapted": adapted["results"],
        "dev_baseline": dev_baseline["results"],
        "dev_adapted": dev_adapted["results"],
        "timing_seconds": {
            "baseline": baseline["seconds"],
            "adapted": adapted["seconds"],
            "training": training_seconds,
        },
    }
    _write_report(output, report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-local", action="store_true", required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/rag-embedding-adaptation/learner")
    )
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    run_local(
        args.model_dir,
        json.loads(args.data.read_text(encoding="utf-8")),
        args.output,
        k=args.k,
        steps=args.steps,
        seed=args.seed,
        provenance=json.loads(args.provenance.read_text(encoding="utf-8")),
    )


if __name__ == "__main__":
    main()
