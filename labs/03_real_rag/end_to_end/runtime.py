"""Actual dense retrieval→provider runner. Offline geometry is not model quality."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from time import perf_counter
from typing import Any

import httpx
import numpy as np

dense = import_module("labs.03_real_rag.dense")
demo = import_module("labs.03_real_rag.demo")
local = import_module("labs.03_real_rag.local_generator")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class Config:
    k: int = 2
    min_score: float = 0.35
    character_budget: int = 2000

    def __post_init__(self) -> None:
        if (
            type(self.k) is not int
            or not 1 <= self.k <= 10
            or type(self.min_score) not in {int, float}
            or not np.isfinite(self.min_score)
            or not -1 <= self.min_score <= 1
            or type(self.character_budget) is not int
            or not 1 <= self.character_budget <= 10000
        ):
            raise ValueError("invalid frozen retrieval configuration")


def teacher_chunks() -> tuple[Any, ...]:
    return tuple(chunk for source in demo.teacher_sources() for chunk in demo.rag.chunks(source))


def teacher_cases() -> list[dict[str, Any]]:
    """Visible author fixtures; final learner evaluation needs independently authored cases."""
    rows = []
    for split, questions in (
        (
            "dev",
            [
                "scanner resolution",
                "volcano insurance",
                "scanner resolution",
                "scanner resolution",
                "What are the settings?",
            ],
        ),
        (
            "holdout",
            [
                "Which dpi is required for paper copies?",
                "Who insures volcanoes?",
                "paper copy resolution",
                "paper copy resolution",
                "Which settings?",
            ],
        ),
    ):
        for kind, question in zip(
            ("answerable", "missing", "acl", "stale", "ambiguous"), questions, strict=True
        ):
            rows.append(
                {
                    "case_id": f"{split}-{kind}",
                    "split": split,
                    "kind": kind,
                    "query": question,
                    # Current metadata is trusted operator input, distinct from answer annotations.
                    "revoked_ids": [c.chunk_id for c in teacher_chunks()] if kind == "acl" else [],
                    "stale_ids": [c.chunk_id for c in teacher_chunks()] if kind == "stale" else [],
                    "relevant_ids": ["A-SCAN@1:p1"] if kind == "answerable" else [],
                    "expected_answers": ["300 dpi"] if kind == "answerable" else [],
                    "should_abstain": kind != "answerable",
                }
            )
    return rows


def validate_cases(cases: list[dict[str, Any]]) -> None:
    if not cases or len(cases) > 1000:
        raise ValueError("bounded nonempty cases required")
    ids = [row["case_id"] for row in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("case IDs must be unique")
    for row in cases:
        if (
            row["split"] not in {"dev", "holdout"}
            or not isinstance(row["query"], str)
            or not row["query"].strip()
            or len(row["query"]) > 1000
            or type(row["should_abstain"]) is not bool
            or any(
                not isinstance(row[key], list)
                or any(not isinstance(item, str) for item in row[key])
                for key in ("relevant_ids", "expected_answers", "revoked_ids", "stale_ids")
            )
        ):
            raise ValueError("invalid query annotations or trusted metadata")

    dev_queries = {" ".join(row["query"].lower().split()) for row in cases if row["split"] == "dev"}
    holdout_queries = {
        " ".join(row["query"].lower().split()) for row in cases if row["split"] == "holdout"
    }
    if dev_queries & holdout_queries:
        raise ValueError("dev/holdout query texts must be disjoint")


def rank(
    case: dict[str, Any],
    chunks: tuple[Any, ...],
    vectors: Any,
    query_vector: Any,
    config: Config,
) -> list[tuple[Any, float]]:
    """Exact cosine: authorize and remove stale chunks before score cutoff/top-k."""
    raw = np.asarray(vectors)
    dimension = raw.shape[1] if raw.ndim == 2 else 0
    matrix = dense.checked_vectors(vectors, rows=len(chunks), dimension=dimension)
    query = dense.checked_vectors([query_vector], rows=1, dimension=dimension)[0]
    revoked, stale = set(case["revoked_ids"]), set(case["stale_ids"])
    eligible = [
        (chunk, float(vector @ query))
        for chunk, vector in zip(chunks, matrix, strict=True)
        if chunk.access == "public" and chunk.chunk_id not in revoked | stale
    ]
    return sorted(
        [(chunk, score) for chunk, score in eligible if score >= config.min_score],
        key=lambda pair: (-pair[1], pair[0].chunk_id),
    )[: config.k]


def needs_clarification(query: str) -> bool:
    """Tiny explicit teaching policy, not a general semantic ambiguity detector."""
    words = set(query.lower().replace("?", "").split())
    return "settings" in words and not words & {"scanner", "scan", "paper", "dpi"}


def answer_metrics(
    answer: dict[str, Any], case: dict[str, Any], passages: tuple[Any, ...]
) -> dict[str, Any]:
    """Independent narrow gold checks; entailment remains a human review requirement."""
    answered = answer["status"] == "answer"
    text = " ".join(answer["text"].lower().split())
    expected = [" ".join(value.lower().split()) for value in case["expected_answers"]]
    correct = answered and text in expected
    by_id = {passage.chunk_id: passage.text.lower() for passage in passages}
    supported = (
        answered
        and bool(answer["citation_ids"])
        and all(
            citation in by_id and text in " ".join(by_id[citation].split())
            for citation in answer["citation_ids"]
        )
    )
    return {
        "correct": correct if expected else None,
        "supported": supported if answered else None,
        "abstention_correct": answer["status"] in {"answer", "no_answer"}
        and ((answer["status"] == "no_answer") == case["should_abstain"]),
        "human_entailment": "REQUIRES_REVIEW",
        "metric_contract": "normalized_exact_answer_and_cited_substring_proxy_v1",
    }


def run_case(
    case: dict[str, Any],
    chunks: tuple[Any, ...],
    vectors: Any,
    query_vector: Any,
    config: Config,
    generator: Callable[..., Any],
) -> dict[str, Any]:
    validate_cases([case])
    started = perf_counter()
    ranked = rank(case, chunks, vectors, query_vector, config)
    retrieval_seconds = perf_counter() - started
    relevant = set(case["relevant_ids"])
    ids = [chunk.chunk_id for chunk, _ in ranked]
    first = next((i for i, item in enumerate(ids, 1) if item in relevant), None)
    passages, used = [], 0
    for chunk, _ in ranked:
        if used + len(chunk.text) <= config.character_budget:
            passages.append(chunk)
            used += len(chunk.text)
    context = tuple(passages)
    called = bool(context) and not needs_clarification(case["query"])
    answer = demo.Answer("", (), "no_answer")
    generation_started = perf_counter()
    if called:
        try:
            draft = generator(case["query"], context)
            valid = (
                isinstance(draft, demo.Draft)
                and isinstance(draft.text, str)
                and 0 < len(draft.text.strip()) <= 6000
                and isinstance(draft.citation_ids, tuple)
                and bool(draft.citation_ids)
                and all(isinstance(item, str) for item in draft.citation_ids)
                and len(set(draft.citation_ids)) == len(draft.citation_ids)
                and set(draft.citation_ids) <= {p.chunk_id for p in context}
            )
            answer = (
                demo.Answer(draft.text, draft.citation_ids, "answer")
                if valid
                else demo.Answer("", (), "invalid_output")
            )
        except demo.ProviderUnavailable:
            answer = demo.Answer("", (), "provider_error")
    actual = asdict(answer)
    prompt = getattr(generator, "last_prompt", None) if called else None
    provider_result = getattr(generator, "last_result", None) if called else None
    return {
        "case_id": case["case_id"],
        "split": case["split"],
        "kind": case["kind"],
        "query": case["query"],
        "query_sha256": digest(case["query"]),
        "retrieved_ids": ids,
        "scores": [score for _, score in ranked],
        "context_ids": [p.chunk_id for p in context],
        "retrieval": {
            "recall_at_k": len(set(ids) & relevant) / len(relevant) if relevant else None,
            "reciprocal_rank": 1 / first if first else (0.0 if relevant else None),
        },
        "answer": actual,
        "answer_metrics": answer_metrics(actual, case, context),
        "generator_called": called,
        "prompt_sha256": digest(prompt) if prompt else None,
        "prompt": prompt,
        "stream": asdict(provider_result) if provider_result is not None else None,
        "retrieval_seconds": retrieval_seconds,
        "generation_seconds": perf_counter() - generation_started,
        "total_seconds": perf_counter() - started,
    }


def tune_threshold(
    dev: list[dict[str, Any]],
    candidates: list[float],
    objective: Callable[[dict[str, Any], float], float],
) -> float:
    validate_cases(dev)
    if any(case["split"] != "dev" for case in dev):
        raise ValueError("tuning accepts dev only")
    if not candidates:
        raise ValueError("threshold candidates required")
    for value in candidates:
        Config(min_score=value)
    return max(
        candidates,
        key=lambda threshold: (
            sum(objective(case, threshold) for case in dev) / len(dev),
            threshold,
        ),
    )


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-split descriptive means with explicit non-null denominators."""
    result = {}
    for split in sorted({row["split"] for row in rows}):
        selected = [row for row in rows if row["split"] == split]
        summary: dict[str, Any] = {"cases": len(selected)}
        for group, names in (
            ("retrieval", ("recall_at_k", "reciprocal_rank")),
            ("answer_metrics", ("correct", "supported", "abstention_correct")),
        ):
            for name in names:
                values = [
                    float(row[group][name]) for row in selected if row[group][name] is not None
                ]
                summary[name] = {
                    "mean": sum(values) / len(values) if values else None,
                    "denominator": len(values),
                }
        summary["provider_errors"] = sum(
            row["answer"]["status"] == "provider_error" for row in selected
        )
        summary["invalid_outputs"] = sum(
            row["answer"]["status"] == "invalid_output" for row in selected
        )
        latency = [row["total_seconds"] for row in selected]
        summary["latency_p50_seconds"] = float(np.percentile(latency, 50))
        summary["latency_p95_seconds"] = float(np.percentile(latency, 95))
        summary["timing_scope"] = (
            "sequential tiny-fixture wall time, excludes encoder; not load test"
        )
        result[split] = summary
    return result


def run_live(
    output: Path,
    model_dir: Path,
    *,
    pooling: str = "masked_mean",
    cases: list[dict[str, Any]] | None = None,
    learner: bool = False,
) -> dict[str, Any]:
    """Explicit networked local experiment; no downloads, no fallback generator."""
    cases = teacher_cases() if cases is None else cases
    validate_cases(cases)
    if {case["split"] for case in cases} != {"dev", "holdout"}:
        raise ValueError("separate dev and holdout required")
    output.mkdir(parents=True, exist_ok=False)
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "evidence_kind": "AUTHOR_LIVE_DENSE_RAG",
        "created_at": datetime.now(UTC).isoformat(),
        "technical_status": "FAILED",
        "quality": "REQUIRES_REVIEW",
        "cases": [],
        "annotations": cases,
        "corpus_sha256": digest([asdict(c) for c in teacher_chunks()]),
        "queries_sha256": digest(cases),
        "generator": {
            "model": local.MODEL,
            "digest": local.MODEL_DIGEST,
            "contract": "labs.03_real_rag.local_generator.LocalGenerator",
        },
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    if learner:
        receipt["evidence_kind"] = "LEARNER_LIVE_DENSE_RAG"
        receipt["learner_source_sha256"] = hashlib.sha256(
            Path(__file__).with_name("starter.py").read_bytes()
        ).hexdigest()
    try:
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=5) as client:
            response = client.get("http://127.0.0.1:11434/api/tags")
            response.raise_for_status()
            receipt["generator"]["metadata_before"] = local.selected_model(
                response.json(), local.MODEL_DIGEST
            )
        chunks = teacher_chunks()
        started = perf_counter()
        vectors, identity = dense.encode_local_minilm(
            model_dir,
            (*[c.text for c in chunks], *[row["query"] for row in cases]),
            pooling=pooling,
        )
        receipt["embedding"] = identity
        receipt["encoding_seconds"] = perf_counter() - started
        documents, queries = vectors[: len(chunks)], vectors[len(chunks) :]
        query_by_id = dict(zip([row["case_id"] for row in cases], queries, strict=True))
        dev = [row for row in cases if row["split"] == "dev"]

        def objective(case: dict[str, Any], threshold: float) -> float:
            # Dev retrieval/policy objective; no gold labels enter the runtime ranker.
            found = rank(
                case, chunks, documents, query_by_id[case["case_id"]], Config(min_score=threshold)
            )
            predicts_answer = bool(found) and not needs_clarification(case["query"])
            return float(predicts_answer != case["should_abstain"])

        threshold = tune_threshold(dev, [0.2, 0.35, 0.5, 0.65, 0.8], objective)
        config = Config(min_score=threshold)
        receipt["config"] = asdict(config)
        receipt["config_sha256"] = digest(receipt["config"])
        receipt["tuning"] = {
            "split": "dev",
            "case_ids": [row["case_id"] for row in dev],
            "objective": "answerability_accuracy",
            "candidates": [0.2, 0.35, 0.5, 0.65, 0.8],
        }
        # Configuration is frozen before the heldout loop. Provider receives passages from rank().
        for row in cases:
            case_runner = (
                import_module(__package__ + ".starter").answer_case if learner else run_case
            )
            receipt["cases"].append(
                case_runner(
                    row,
                    chunks,
                    documents,
                    query_by_id[row["case_id"]],
                    config,
                    local.LocalGenerator(),
                )
            )
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=5) as client:
            response = client.get("http://127.0.0.1:11434/api/tags")
            response.raise_for_status()
            local.selected_model(response.json(), local.MODEL_DIGEST)
        receipt["identity_unchanged"] = True
        receipt["summary"] = summarize(receipt["cases"])
        receipt["technical_status"] = "PASS"
    except (httpx.HTTPError, ValueError, RuntimeError, ImportError, OSError) as exc:
        receipt["error_type"] = type(exc).__name__
        receipt["error"] = str(exc)
    finally:
        (output / "receipt.json").write_bytes(canonical(receipt) + b"\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-local", required=True, action="store_true")
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--pooling", choices=("cls", "masked_mean"), default="masked_mean")
    parser.add_argument(
        "--learner", action="store_true", help="Execute independent starter.answer_case"
    )
    parser.add_argument(
        "--cases", type=Path, help="Independent JSON case list; same annotation schema"
    )
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8")) if args.cases else None
    receipt = run_live(
        args.output, args.model_dir, pooling=args.pooling, cases=cases, learner=args.learner
    )
    print(
        json.dumps({"technical_status": receipt["technical_status"], "quality": receipt["quality"]})
    )
    if receipt["technical_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
