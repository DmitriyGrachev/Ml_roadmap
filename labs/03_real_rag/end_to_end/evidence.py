"""Read-only live evidence checks; integrity/consistency do not authenticate execution."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

from . import runtime as rt


def _checked_context(
    row: dict[str, Any], annotation: dict[str, Any], chunks: dict[str, Any], config: rt.Config
) -> tuple[Any, ...]:
    """Bind the recorded ranking to the same deterministic context/provider policy.

    This checks consistency of recorded cosine values, not their origin: reproducing
    embeddings remains part of the independent human gate. A tiny cosine tolerance
    accommodates floating-point dot products just beyond +/-1 after normalization.
    """
    ranked, scores, context_ids = row["retrieved_ids"], row["scores"], row["context_ids"]
    forbidden = set(annotation["revoked_ids"]) | set(annotation["stale_ids"])
    if (
        not isinstance(ranked, list)
        or not isinstance(scores, list)
        or not isinstance(context_ids, list)
        or len(ranked) != len(scores)
        or len(ranked) > config.k
        or any(not isinstance(item, str) for item in ranked)
        or len(set(ranked)) != len(ranked)
        or any(
            item not in chunks or chunks[item].access != "public" or item in forbidden
            for item in ranked
        )
    ):
        raise ValueError(
            "ranked retrieval requires unique known eligible IDs and aligned scores within k"
        )
    if any(
        type(score) not in {int, float}
        or not -1.0 - 1e-12 <= score <= 1.0 + 1e-12
        or not math.isfinite(score)
        or score < config.min_score
        for score in scores
    ):
        raise ValueError(
            "retrieval scores must be finite cosine values meeting the configured cutoff"
        )
    pairs = list(zip(ranked, scores, strict=True))
    if pairs != sorted(pairs, key=lambda pair: (-pair[1], pair[0])):
        raise ValueError("retrieval must be ranked by descending cosine then ascending chunk ID")
    expected_ids, used = [], 0
    for item in ranked:
        if used + len(chunks[item].text) <= config.character_budget:
            expected_ids.append(item)
            used += len(chunks[item].text)
    if context_ids != expected_ids:
        raise ValueError("provider context must equal the budgeted selection from ranked retrieval")
    should_call = bool(context_ids) and not rt.needs_clarification(row["query"])
    if type(row["generator_called"]) is not bool or row["generator_called"] != should_call:
        raise ValueError("provider call must agree with available context and clarification policy")
    answer = row["answer"]
    if should_call:
        if answer["status"] not in {"answer", "invalid_output", "provider_error"}:
            raise ValueError(
                "provider call requires a provider answer or explicit provider failure"
            )
    elif answer["status"] != "no_answer" or row["stream"] is not None:
        raise ValueError("gated context must not claim a provider result")
    if answer["status"] == "answer":
        citations = answer["citation_ids"]
        if (
            not isinstance(answer["text"], str)
            or not 0 < len(answer["text"].strip()) <= 6000
            or not isinstance(citations, list)
            or not citations
            or any(not isinstance(item, str) for item in citations)
            or len(set(citations)) != len(citations)
            or not set(citations) <= set(context_ids)
        ):
            raise ValueError("provider answer must cite only its actual context")
    elif answer["text"] != "" or answer["citation_ids"] != []:
        raise ValueError("non-answer statuses require an empty answer and citations")
    return tuple(chunks[item] for item in context_ids)


def validate_submission(root: Path) -> None:
    """Require independent actual runs in both representations plus human review material.

    Never executes saved Python or contacts a provider. A dishonest author could
    fabricate JSON; examiner re-running the trusted learner code is the final gate.
    Poor quality is permitted, missing experiments are not.
    """
    try:
        review = json.loads((root / "review.json").read_text(encoding="utf-8"))
        if review["status"] != "REQUIRES_REVIEW":
            raise ValueError("review must remain REQUIRES_REVIEW")
        for field in (
            "hypothesis",
            "dev_selection",
            "retrieval_vs_answers",
            "failure_analysis",
            "uncertainty",
            "transfer",
            "human_support_review",
        ):
            if not isinstance(review[field], str) or len(review[field].strip()) < 40:
                raise ValueError("substantial independent review required")
        reports = [
            json.loads((root / name).read_text(encoding="utf-8"))
            for name in ("cls.json", "masked_mean.json")
        ]
        learner_hash = hashlib.sha256(
            Path(__file__).with_name("starter.py").read_bytes()
        ).hexdigest()
        teacher_queries = {row["query"] for row in rt.teacher_cases()}
        previous_cases = None
        for report, pooling in zip(
            reports,
            ("first-token-last-hidden-state-l2-v1", "attention-mask-mean-last-hidden-state-l2-v1"),
            strict=True,
        ):
            if (
                report["evidence_kind"] != "LEARNER_LIVE_DENSE_RAG"
                or report["technical_status"] != "PASS"
                or report["learner_source_sha256"] != learner_hash
                or report["embedding"]["pooling"] != pooling
                or report["generator"]["model"] != rt.local.MODEL
                or report["generator"]["digest"] != rt.local.MODEL_DIGEST
                or report["identity_unchanged"] is not True
            ):
                raise ValueError("actual learner encoder and generator identity required")
            # Re-use the pinned artifact identity instead of trusting only a human label.
            model = rt.dense.import_module(
                "labs.02_huggingface_models.download"
            ).resource_manifest()["model"]
            if (
                report["embedding"]["model"] != model["id"]
                or report["embedding"]["revision"] != model["revision"]
                or report["embedding"]["files"] != model["files"]
            ):
                raise ValueError("pinned pretrained model identity required")
            annotations = report["annotations"]
            rt.validate_cases(annotations)
            if len(annotations) < 10 or any(row["query"] in teacher_queries for row in annotations):
                raise ValueError("independent dev/holdout cases required")
            if previous_cases is not None and annotations != previous_cases:
                raise ValueError("paired pooling comparison requires identical cases")
            previous_cases = annotations
            dev_ids = {row["case_id"] for row in annotations if row["split"] == "dev"}
            if (
                report["tuning"]["split"] != "dev"
                or set(report["tuning"]["case_ids"]) != dev_ids
                or report["config_sha256"] != rt.digest(report["config"])
                or report["queries_sha256"] != rt.digest(annotations)
                or report["corpus_sha256"] != rt.digest([asdict(c) for c in rt.teacher_chunks()])
            ):
                raise ValueError("frozen dev-only configuration and artifact hashes required")
            config = rt.Config(**report["config"])
            by_id = {row["case_id"]: row for row in annotations}
            rows = report["cases"]
            if len(rows) != len(by_id) or {row["case_id"] for row in rows} != set(by_id):
                raise ValueError("every case must be recorded exactly once")
            chunks = {chunk.chunk_id: chunk for chunk in rt.teacher_chunks()}
            for split in ("dev", "holdout"):
                selected = [row for row in rows if row["split"] == split]
                if not {"answerable", "missing", "acl", "stale", "ambiguous"} <= {
                    row["kind"] for row in selected
                }:
                    raise ValueError("both splits need every policy scenario")
                if not any(
                    row["generator_called"] and row["stream"]["status"] == "ok" for row in selected
                ):
                    raise ValueError("successful live provider call required in each split")
            for row in rows:
                annotation = by_id[row["case_id"]]
                if (
                    row["query"] != annotation["query"]
                    or row["split"] != annotation["split"]
                    or row["kind"] != annotation["kind"]
                ):
                    raise ValueError("case/annotation correspondence mismatch")
                if row["query_sha256"] != rt.digest(row["query"]):
                    raise ValueError("query hash mismatch")
                if row["generator_called"]:
                    if not row["prompt"] or row["prompt_sha256"] != rt.digest(row["prompt"]):
                        raise ValueError("actual prompt hash required")
                elif row["prompt"] is not None or row["prompt_sha256"] is not None:
                    raise ValueError("gated case cannot claim a provider prompt")
                for key in ("retrieval_seconds", "generation_seconds", "total_seconds"):
                    value = row[key]
                    if type(value) not in {float, int} or not 0 <= value < 3600:
                        raise ValueError("finite bounded measured case latency required")
                passages = _checked_context(row, annotation, chunks, config)
                expected_metrics = rt.answer_metrics(row["answer"], annotation, passages)
                if row["answer_metrics"] != expected_metrics:
                    raise ValueError("answer metrics must be independently recomputable")
                relevant = set(annotation["relevant_ids"])
                ranked = row["retrieved_ids"]
                recall = len(set(ranked) & relevant) / len(relevant) if relevant else None
                first = next((i for i, item in enumerate(ranked, 1) if item in relevant), None)
                rr = 1 / first if first else (0.0 if relevant else None)
                if row["retrieval"] != {"recall_at_k": recall, "reciprocal_rank": rr}:
                    raise ValueError("retrieval metrics must be independently recomputable")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"invalid or incomplete live learner evidence: {exc}") from exc
