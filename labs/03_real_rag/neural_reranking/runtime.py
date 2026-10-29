"""Explicit local model and evidence IO; no model imports on ordinary import."""

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
    """Bound encoded UTF-8 incrementally, before opening any successful report."""
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


def _preflight_report(data: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
    """Account for repeated candidate text and widest scalar encodings before inference."""
    widest_float = -1.2345678901234567e-123
    documents = {row["id"]: row for row in data["corpus"]}
    metrics = {
        row["query_id"]: dict.fromkeys(("candidate_recall", "mrr_at_k", "ndcg_at_k"), widest_float)
        for row in data["queries"]
    }
    _report_bytes(
        {
            "data": data,
            "rows": [
                {
                    "query_id": row["query_id"],
                    "ranking": [
                        {**documents[doc_id], "score": widest_float}
                        for doc_id in row["candidate_ids"]
                    ],
                    "seconds": widest_float,
                }
                for row in data["queries"]
            ],
            "metrics": metrics,
            "baseline_metrics": metrics,
            "known_metadata": metadata or {},
            "reserved_metadata": " " * REPORT_METADATA_RESERVE_BYTES,
        }
    )


def _require(condition: object) -> None:
    if not condition:
        raise ValueError("contract requirement failed")


def validate_cases(data: dict[str, Any]) -> None:
    """Bounded inputs; qrels never enter the pair scorer."""
    try:
        corpus, queries, qrels = data["corpus"], data["queries"], data["qrels"]
        _require(1 <= len(corpus) <= 5000 and 2 <= len(queries) <= 1000)
        ids = [row["id"] for row in corpus]
        _require(len(ids) == len(set(ids)))
        _require(all(isinstance(i, str) and i.strip() for i in ids))
        _require(
            all(isinstance(row["text"], str) and 0 < len(row["text"]) <= 10000 for row in corpus)
        )
        query_ids = [row["query_id"] for row in queries]
        _require(len(query_ids) == len(set(query_ids)))
        _require(all(isinstance(i, str) and i.strip() for i in query_ids))
        _require(set(query_ids) == set(qrels))
        _require({row["split"] for row in queries} == {"dev", "holdout"})
        normalized = [" ".join(row["query"].casefold().split()) for row in queries]
        _require(all(normalized) and len(normalized) == len(set(normalized)))
        for row in queries:
            candidates = row["candidate_ids"]
            _require(isinstance(candidates, list) and len(candidates) <= 200)
            _require(len(candidates) == len(set(candidates)) and set(candidates) <= set(ids))
            _require(len(row["query"]) <= 1000)
            _require(set(qrels[row["query_id"]]) <= set(ids))
            _require(all(type(g) is int and 0 <= g <= 4 for g in qrels[row["query_id"]].values()))
    except (AssertionError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError("invalid bounded ranking data or query isolation") from exc
    _preflight_report(data)


def local_scorer(directory: Path) -> Any:
    """Return actual CPU CrossEncoder with one scalar logit per pair."""
    if not directory.is_dir() or not (directory / "config.json").is_file():
        raise ValueError("explicit existing local model directory required")
    try:
        cls = import_module("sentence_transformers").CrossEncoder
        torch = import_module("torch")
    except ImportError as exc:
        raise RuntimeError("Install optional ranking group: uv sync --group ranking") from exc
    torch.set_num_threads(1)
    model = cls(
        str(directory.resolve()), device="cpu", local_files_only=True, trust_remote_code=False
    )
    if model.num_labels != 1:
        raise ValueError("local reranker must produce exactly one scalar score per pair")
    # A logit is sufficient for ordering; never silently interpret multi-class columns.
    model.activation_fn = torch.nn.Identity()
    return model


def snapshot(directory: Path) -> dict[str, str]:
    """Hash a bounded local snapshot; no remote lookup or unsafe pickle execution."""
    if not directory.is_dir():
        raise ValueError("explicit local snapshot required")
    files = sorted(p for p in directory.rglob("*") if p.is_file())
    if not files or len(files) > 1000 or sum(p.stat().st_size for p in files) > 2_000_000_000:
        raise ValueError("snapshot exceeds local lab budget")
    if any(p.is_symlink() or p.suffix in {".bin", ".pt", ".pth"} for p in files):
        raise ValueError("use local safetensors snapshot without symlinks/pickle weights")
    return {
        str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
    }


def run_local(
    model_dir: Path, data: dict[str, Any], output: Path, *, k: int, provenance: dict[str, Any]
) -> None:
    """Run learner code against explicit local weights; new output directory only."""
    validate_cases(data)
    if type(k) is not int or not 1 <= k <= 200:
        raise ValueError("k must be an integer in 1..200")
    if provenance.get("kind") != "pretrained" or not all(
        provenance.get(x) for x in ("model_id", "revision", "license")
    ):
        raise ValueError("declare independently reviewed pretrained provenance")
    manifest = snapshot(model_dir)
    _preflight_report(data, {"snapshot": manifest, "provenance": provenance})
    model = local_scorer(model_dir)
    learner = import_module(__package__ + ".starter")
    output.mkdir(parents=True, exist_ok=False)
    documents = {r["id"]: r for r in data["corpus"]}
    rankings, rows = {}, []
    for query in data["queries"]:
        candidates = [documents[i] for i in query["candidate_ids"]]
        started = perf_counter()
        ranked = learner.rerank(
            query["query"],
            candidates,
            lambda pairs: model.predict(pairs, batch_size=8, show_progress_bar=False).tolist(),
            max(1, len(candidates)),
        )
        rankings[query["query_id"]] = [r["id"] for r in ranked]
        rows.append(
            {"query_id": query["query_id"], "ranking": ranked, "seconds": perf_counter() - started}
        )
    report = {
        "evidence_kind": "LEARNER_LOCAL_PRETRAINED_RERANKING",
        "status": "PASS",
        "quality": "REQUIRES_REVIEW",
        "k": k,
        "data": data,
        "rows": rows,
        "metrics": learner.ranking_metrics(rankings, data["qrels"], k),
        "baseline_metrics": learner.ranking_metrics(
            {q["query_id"]: q["candidate_ids"] for q in data["queries"]}, data["qrels"], k
        ),
        "provenance": provenance,
        "snapshot": manifest,
        "learner_source_sha256": hashlib.sha256(
            Path(__file__).with_name("starter.py").read_bytes()
        ).hexdigest(),
    }
    _write_report(output, report)


def validate_submission(directory: Path) -> None:
    """Read-only consistency gate; provenance and execution require human rerun."""
    try:
        path = directory / "report.json"
        _require(path.stat().st_size <= MAX_REPORT_BYTES)
        report = json.loads(path.read_text(encoding="utf-8"))
        _require(report["evidence_kind"] == "LEARNER_LOCAL_PRETRAINED_RERANKING")
        _require(report["status"] == "PASS" and report["quality"] == "REQUIRES_REVIEW")
        _require(
            report["learner_source_sha256"]
            == hashlib.sha256(Path(__file__).with_name("starter.py").read_bytes()).hexdigest()
        )
        _require(report["provenance"]["kind"] == "pretrained" and report["snapshot"])
        _require(all(report["provenance"].get(x) for x in ("model_id", "revision", "license")))
        validate_cases(report["data"])
        queries = {r["query_id"]: r for r in report["data"]["queries"]}
        _require(len(report["rows"]) == len(queries))
        _require({r["query_id"] for r in report["rows"]} == set(queries))
        _require(type(report["k"]) is int and 1 <= report["k"] <= 200)
        corpus = {r["id"]: r["text"] for r in report["data"]["corpus"]}
        for row in report["rows"]:
            ranked = row["ranking"]
            ids = [r["id"] for r in ranked]
            _require(
                len(ids) == len(set(ids))
                and len(ids) == len(queries[row["query_id"]]["candidate_ids"])
            )
            _require(set(ids) <= set(queries[row["query_id"]]["candidate_ids"]))
            _require(
                all(
                    r["text"] == corpus[r["id"]]
                    and type(r["score"]) in {int, float}
                    and math.isfinite(r["score"])
                    for r in ranked
                )
            )
            _require(ranked == sorted(ranked, key=lambda r: (-r["score"], r["id"])))
            _require(
                type(row["seconds"]) in {int, float}
                and math.isfinite(row["seconds"])
                and row["seconds"] >= 0
            )
        for name in ("metrics", "baseline_metrics"):
            _require(set(report[name]) == set(queries))
            for qid, metrics in report[name].items():
                _require(set(metrics) == {"candidate_recall", "mrr_at_k", "ndcg_at_k"})
                relevant = any(g > 0 for g in report["data"]["qrels"][qid].values())
                _require(
                    all(
                        (type(v) in {int, float} and math.isfinite(v) and 0 <= v <= 1)
                        if relevant
                        else v is None
                        for v in metrics.values()
                    )
                )
                if relevant:
                    # Integrity calculation only: this validator returns no ranking/metrics
                    # that could substitute for either independent learner function.
                    grades = report["data"]["qrels"][qid]
                    pool = (
                        queries[qid]["candidate_ids"]
                        if name == "baseline_metrics"
                        else next(
                            [r["id"] for r in row["ranking"]]
                            for row in report["rows"]
                            if row["query_id"] == qid
                        )
                    )
                    positive_ids = {doc_id for doc_id, grade in grades.items() if grade > 0}
                    first = next(
                        (
                            i
                            for i, doc_id in enumerate(pool[: report["k"]], 1)
                            if doc_id in positive_ids
                        ),
                        None,
                    )
                    dcg = sum(
                        (2 ** grades.get(doc_id, 0) - 1) / math.log2(i + 1)
                        for i, doc_id in enumerate(pool[: report["k"]], 1)
                    )
                    ideal = sum(
                        (2**grade - 1) / math.log2(i + 1)
                        for i, grade in enumerate(
                            sorted(grades.values(), reverse=True)[: report["k"]], 1
                        )
                    )
                    expected = {
                        "candidate_recall": len(set(pool) & positive_ids) / len(positive_ids),
                        "mrr_at_k": 1 / first if first else 0.0,
                        "ndcg_at_k": dcg / ideal,
                    }
                    _require(
                        all(abs(metrics[key] - value) <= 1e-8 for key, value in expected.items())
                    )
        review = json.loads((directory / "review.json").read_text(encoding="utf-8"))
        _require(review["status"] == "REQUIRES_REVIEW")
        _require(
            all(
                isinstance(review.get(k), str) and len(review[k].strip()) >= 40
                for k in (
                    "candidate_ceiling",
                    "failure_analysis",
                    "cost",
                    "transfer",
                    "provenance_review",
                )
            )
        )
    except (AssertionError, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ValueError(
            "reranking evidence is missing or inconsistent; independent review required"
        ) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-local", action="store_true", required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/rag-neural-reranking/learner")
    )
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    run_local(
        args.model_dir,
        json.loads(args.data.read_text(encoding="utf-8")),
        args.output,
        k=args.k,
        provenance=json.loads(args.provenance.read_text(encoding="utf-8")),
    )


if __name__ == "__main__":
    main()
