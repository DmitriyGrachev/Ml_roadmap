"""Check a saved learner experiment without contacting a model or trace collector."""

import json
from dataclasses import fields
from pathlib import Path
from typing import Any

from .run import CORPUS, DEFAULT_CASES, load_cases, norm, public_passages
from .scoring import Observation, metrics, violations
from .service import digest


def _check_trace(payload: dict[str, Any], trace_id: str, case_id: str, release: str) -> None:
    spans = [
        span
        for group in payload["resourceSpans"]
        for scope in group["scopeSpans"]
        for span in scope["spans"]
        if span["traceId"] == trace_id
    ]
    by_name = {span["name"]: span for span in spans}
    if len(spans) != 3 or set(by_name) != {"document.answer", "retrieval", "generation"}:
        raise ValueError("reviewed trace must cover the request, retrieval and generation")
    request = by_name["document.answer"]
    tags = {item["key"]: item["value"]["stringValue"] for item in request["attributes"]}
    if tags.get("eval.case_id") != case_id or tags.get("eval.release") != release:
        raise ValueError("reviewed trace belongs to a different case or release")
    if any(by_name[k]["parentSpanId"] != request["spanId"] for k in ("retrieval", "generation")):
        raise ValueError("reviewed stages must belong to the same request")


def validate_submission(folder: Path) -> None:
    if not folder.exists():
        raise NotImplementedError("Run your independent release evaluation and add its review.")
    report = json.loads((folder / "report.json").read_bytes())
    if (report["mode"], report["usage_unit"], report["api_transport"]) != (
        "local",
        "provider_tokens",
        "loopback_http",
    ):
        raise ValueError("a live model run is required for learner credit")
    case_bytes = (folder / "cases.json").read_bytes()
    traces = (folder / "traces.json").read_bytes()
    corpus = CORPUS.read_bytes()
    if (
        digest(case_bytes) != report["data_sha256"]
        or digest(corpus) != report["corpus_sha256"]
        or digest(traces) != report["traces_sha256"]
    ):
        raise ValueError("evidence digests do not match the recorded run")
    cases = load_cases(case_bytes, {p.chunk_id for p in public_passages(corpus)}, teacher=False)
    examples = {norm(r["text"]) for r in json.loads(DEFAULT_CASES.read_bytes())["queries"]}
    if all(norm(case.query) in examples for case in cases):
        raise ValueError("include at least one independent question in your evaluation")

    labels = {case.case_id: case.answerable for case in cases}
    observations: dict[str, list[Observation]] = {}
    for side in ("baseline", "candidate"):
        section = report[side]
        model = section["model"]
        if not all(isinstance(model[k], str) and model[k].strip() for k in ("id", "revision")):
            raise ValueError(f"{side} model identity is missing")
        rows = [
            Observation(**{field.name: row[field.name] for field in fields(Observation)})
            for row in section["cases"]
        ]
        if {row.case_id: row.answerable for row in rows} != labels:
            raise ValueError("case annotations differ from the submitted dataset")
        pricing = section["pricing"]
        measured = metrics(
            rows, pricing["input_usd_per_million"], pricing["output_usd_per_million"]
        )
        if measured != section["metrics"]:
            raise ValueError("reported metrics differ from the recorded observations")
        observations[side] = rows
    if not any(row.output_units for rows in observations.values() for row in rows):
        raise ValueError("no measured model completions")
    reasons = violations(observations["baseline"], observations["candidate"], **report["limits"])
    if reasons != report["violations"] or report["passed"] is not (not reasons):
        raise ValueError("release decision differs from the measured gate")

    review = json.loads((folder / "review.json").read_bytes())
    decision = review["release_decision"]
    if decision not in {"ship", "hold"} or (reasons and decision != "hold"):
        raise ValueError("review must address a failed gate before release")
    if not all(
        isinstance(review[k], str) and review[k].strip() for k in ("diagnosis", "rationale")
    ):
        raise ValueError("explain the trace and the release decision in your own words")
    candidate = {row.case_id: row.trace_id for row in observations["candidate"]}
    if review["case_id"] not in candidate or candidate[review["case_id"]] != review["trace_id"]:
        raise ValueError("review must identify a measured candidate case and its trace")
    _check_trace(
        json.loads(traces), review["trace_id"], review["case_id"], report["candidate"]["name"]
    )
