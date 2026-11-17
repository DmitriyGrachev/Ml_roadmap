"""Compare two releases on the same questions, through the same document API."""

from __future__ import annotations

import argparse
import json
import math
import os
from contextlib import nullcontext
from dataclasses import asdict, dataclass
from http.client import HTTPException
from pathlib import Path
from time import perf_counter_ns
from typing import Any

from .scoring import Observation, metrics, violations
from .service import (
    ID,
    PROMPT,
    RELEASES,
    AnswerAPI,
    Generator,
    Passage,
    digest,
    excerpt,
    local_generator,
    serve_api,
)
from .telemetry import Telemetry, validate_endpoint

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIXTURES = ROOT / "labs" / "03_real_rag" / "fixtures"
CORPUS = FIXTURES / "corpus.json"
DEFAULT_CASES = FIXTURES / "queries.json"
DEFAULT_FRAGMENTS = {
    "q-exact": ["300 dpi"],
    "q-paraphrase": ["300 dpi"],
    "q-hours": ["10:00 to 16:00"],
    "q-absent": [],
    "q-protected": [],
}


def encode(document: object) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


@dataclass(frozen=True)
class Case:
    case_id: str
    query: str
    answerable: bool
    relevant: tuple[str, ...]
    fragments: tuple[str, ...]


def load_cases(raw: bytes, available: set[str], *, teacher: bool) -> list[Case]:
    document = json.loads(raw)
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1:
        raise ValueError("invalid case schema")
    rows = document["queries"]
    if not isinstance(rows, list) or not 2 <= len(rows) <= 100:
        raise ValueError("expected 2 to 100 cases")
    cases: list[Case] = []
    for row in rows:
        key, query, answerable = row["query_id"], row["text"], row["answerable"]
        ids = row["relevant_chunk_ids"]
        fragments = DEFAULT_FRAGMENTS[key] if teacher else row["answer_fragments"]
        if (
            not isinstance(key, str)
            or not ID.fullmatch(key)
            or not isinstance(query, str)
            or not 1 <= len(query.strip()) <= 1000
            or type(answerable) is not bool
            or not isinstance(ids, list)
            or not all(isinstance(i, str) and i in available for i in ids)
            or not isinstance(fragments, list)
            or not all(isinstance(f, str) and f.strip() for f in fragments)
            or bool(ids) != answerable
            or bool(fragments) != answerable
        ):
            raise ValueError("invalid case annotation")
        cases.append(Case(key, query, answerable, tuple(ids), tuple(fragments)))
    if len({c.case_id for c in cases}) != len(cases) or {c.answerable for c in cases} != {
        True,
        False,
    }:
        raise ValueError("need unique case IDs and both answerability slices")
    return cases


def public_passages(raw: bytes) -> list[Passage]:
    result = []
    for source in json.loads(raw)["sources"]:
        if source["access"] == "public":
            # All sources in this fixed snapshot consist of exactly one paragraph.
            source_id = source["source_id"]
            result.append(
                Passage(f"{source_id}@{source['revision']}:p1", source_id, source["raw_text"])
            )
    return result


def norm(s: str) -> str:
    return " ".join(s.casefold().split())


def evaluate(
    api: AnswerAPI,
    cases: list[Case],
    *,
    live: bool,
    save_answers: bool,
) -> tuple[list[Observation], list[dict[str, Any]]]:
    observations, evidence = [], []
    sources = {p.chunk_id: p.text for p in api.passages}
    with serve_api(api) if live else nullcontext(api.answer) as call:
        for case in cases:
            start = perf_counter_ns()
            pred = call(case.case_id, case.query)
            latency = (perf_counter_ns() - start) / 1e6
            # Only the scorer sees annotations. Ranking and generation take the question alone.
            hit = bool(set(pred["retrieved_ids"]).intersection(case.relevant))
            answer, cite = norm(pred["answer"]), pred["citation"]
            grounded = (
                pred["status"] == "answer"
                and bool(answer)
                and cite in case.relevant
                and answer in norm(sources[cite])
                and any(norm(fragment) in answer for fragment in case.fragments)
            )
            correct = grounded if case.answerable else pred["status"] == "no_answer"
            row = Observation(
                case.case_id,
                pred["trace_id"],
                "answerable" if case.answerable else "no_answer",
                case.answerable,
                hit,
                correct,
                latency,
                pred["input_units"],
                pred["output_units"],
            )
            observations.append(row)
            evidence.append(
                {
                    **asdict(row),
                    "status": pred["status"],
                    "citation": cite,
                    "retrieved_ids": pred["retrieved_ids"],
                    "context_ids": pred["context_ids"],
                    "answer_sha256": digest(pred["answer"].encode()),
                }
            )
            if save_answers:
                evidence[-1]["answer"] = pred["answer"]
    return observations, evidence


def arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--candidate", choices=("candidate", "regressed", "matched"), default="candidate"
    )
    parser.add_argument("--mode", choices=("offline", "local"), default="offline")
    parser.add_argument("--cases", type=Path, help="independent labeled questions JSON")
    parser.add_argument("--endpoint", help="full loopback /v1/chat/completions URL")
    parser.add_argument("--model", help="served alias, matched against every provider response")
    parser.add_argument("--model-revision", help="operator-provided revision or model file SHA-256")
    parser.add_argument("--candidate-model")
    parser.add_argument("--candidate-model-revision")
    parser.add_argument("--candidate-endpoint", help="defaults to the same local model server")
    parser.add_argument("--otlp-endpoint", help="full loopback /v1/traces URL")
    parser.add_argument("--input-usd-per-million", type=float)
    parser.add_argument("--output-usd-per-million", type=float)
    parser.add_argument("--candidate-input-usd-per-million", type=float)
    parser.add_argument("--candidate-output-usd-per-million", type=float)
    parser.add_argument("--max-p95-ms", type=float)
    parser.add_argument("--max-output-units", type=int)
    parser.add_argument("--save-answers", action="store_true", help="include answer text in report")
    return parser.parse_args(argv)


@dataclass
class Provider:
    identity: dict[str, str]
    generate: Generator
    prices: tuple[float | None, float | None]

    @property
    def pricing(self) -> dict[str, float | None]:
        return dict(
            zip(("input_usd_per_million", "output_usd_per_million"), self.prices, strict=True)
        )


def providers(args: argparse.Namespace) -> tuple[Provider, Provider]:
    live = args.mode == "local"
    prices = (args.input_usd_per_million, args.output_usd_per_million)
    override_prices = (args.candidate_input_usd_per_million, args.candidate_output_usd_per_million)
    for inp, out in (prices, override_prices):
        if (inp is None) != (out is None) or any(
            amount is not None and (not math.isfinite(amount) or amount < 0)
            for amount in (inp, out)
        ):
            raise ValueError("prices must be a pair of finite nonnegative numbers")
    override = (args.candidate_model, args.candidate_model_revision, args.candidate_endpoint)
    if not live:
        if any(
            x is not None
            for x in (
                args.endpoint,
                args.model,
                args.model_revision,
                *override,
                *prices,
                *override_prices,
            )
        ):
            raise ValueError("model settings and token prices require --mode local")
        offline = Provider({"id": "extractive-first-sentence", "revision": "1"}, excerpt, prices)
        return offline, offline
    if not args.endpoint:
        raise ValueError("local mode requires a chat completions endpoint")
    endpoint = validate_endpoint(args.endpoint, "/v1/chat/completions")
    if not all(isinstance(x, str) and x.strip() for x in (args.model, args.model_revision)):
        raise ValueError("local mode requires a model and a revision")
    if any(x is not None for x in override) and not all(
        isinstance(x, str) and x.strip() for x in override[:2]
    ):
        raise ValueError("candidate override requires a model and a revision")
    endpoint2 = validate_endpoint(args.candidate_endpoint or endpoint, "/v1/chat/completions")
    key = os.getenv("RELEASE_EVAL_API_KEY")
    key2 = os.getenv("RELEASE_EVAL_CANDIDATE_API_KEY", key if endpoint == endpoint2 else None)
    model2 = args.candidate_model or args.model
    revision2 = args.candidate_model_revision or args.model_revision
    return (
        Provider(
            {"id": args.model, "revision": args.model_revision},
            local_generator(endpoint, args.model, key),
            prices,
        ),
        Provider(
            {"id": model2, "revision": revision2},
            local_generator(endpoint2, model2, key2),
            prices if override_prices == (None, None) else override_prices,
        ),
    )


def run(args: argparse.Namespace, telemetry: Telemetry) -> dict[str, Any]:
    live = args.mode == "local"
    before, after = providers(args)
    if args.otlp_endpoint:
        validate_endpoint(args.otlp_endpoint, "/v1/traces")
    raw_corpus = CORPUS.read_bytes()
    raw_cases = (args.cases or DEFAULT_CASES).read_bytes()
    passages = public_passages(raw_corpus)
    cases = load_cases(raw_cases, {p.chunk_id for p in passages}, teacher=args.cases is None)
    limits = {"max_p95_ms": args.max_p95_ms, "max_output_units": args.max_output_units}
    if args.max_p95_ms is not None and (not math.isfinite(args.max_p95_ms) or args.max_p95_ms < 0):
        raise ValueError("invalid latency budget")
    if args.max_output_units is not None and args.max_output_units < 0:
        raise ValueError("invalid output budget")
    data = digest(raw_cases)
    protocol = {
        "dataset": data,
        "corpus": digest(raw_corpus),
        "prompt": PROMPT,
        "baseline": asdict(RELEASES["baseline"]),
        "candidate": asdict(RELEASES[args.candidate]),
        "models": [before.identity, after.identity],
        "limits": limits,
        "scorer": "cited_verbatim_with_gold_fragment_v1",
        "gate": "no_lost_case_or_hit;2/3_answerable;all_abstentions;optional_budgets_v1",
    }
    source_files = [
        HERE / name for name in ("run.py", "service.py", "scoring.py", "telemetry.py")
    ] + [ROOT / "modules/06_rag/05_grounded_answers/example.py"]
    report: dict[str, Any] = {
        "schema_version": 1,
        "mode": args.mode,
        "api_transport": "loopback_http" if live else "in_process",
        "usage_unit": "provider_tokens" if live else "whitespace_proxy",
        "model": before.identity,
        "data_sha256": data,
        "corpus_sha256": protocol["corpus"],
        "protocol_sha256": digest(encode(protocol)),
        "source_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in source_files
        },
        "prompt_sha256": digest(PROMPT.encode()),
        "pricing": before.pricing,
        "limits": limits,
    }
    rows = {}
    for side, release, provider in (
        ("baseline", RELEASES["baseline"], before),
        ("candidate", RELEASES[args.candidate], after),
    ):
        api = AnswerAPI(passages, release, provider.generate, telemetry)
        observations, evidence = evaluate(api, cases, live=live, save_answers=args.save_answers)
        rows[side] = observations
        report[side] = {
            "name": release.name,
            "config": asdict(release),
            "model": provider.identity,
            "pricing": provider.pricing,
            "metrics": metrics(observations, *provider.prices),
            "cases": evidence,
        }
    failures = violations(rows["baseline"], rows["candidate"], **limits)
    report.update(passed=not failures, violations=failures)
    return report


def main(argv: list[str] | None = None) -> int:
    args = arguments(argv)
    out: Path = args.output_dir
    try:
        out.mkdir(parents=True, exist_ok=False)
    except OSError:
        print("A fresh writable output directory is required.")
        return 2
    telemetry = Telemetry()
    try:
        report = run(args, telemetry)
        traces = encode(telemetry.payload())
        (out / "traces.json").write_bytes(traces)
        if args.otlp_endpoint:
            telemetry.export(args.otlp_endpoint)
        report["otlp_exported"] = bool(args.otlp_endpoint)
        report["traces_sha256"] = digest(traces)
        (out / "report.json").write_bytes(encode(report))
        summary = {
            "passed": report["passed"],
            "violations": report["violations"],
            "baseline": report["baseline"]["metrics"],
            "candidate": report["candidate"]["metrics"],
        }
        print(json.dumps(summary))
        return 0 if report["passed"] else 1
    except (ValueError, OSError, KeyError, TypeError, AttributeError, HTTPException) as exc:
        # Provider/OS error text can contain request data; keep raw messages out of evidence.
        failure = {"mode": args.mode, "passed": False, "error_type": type(exc).__name__}
        print(json.dumps(failure))
        (out / "traces.json").write_bytes(encode(telemetry.payload()))
        (out / "failure.json").write_bytes(encode(failure))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
