"""Author infrastructure tests; never included in learner catalog completion."""

from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import numpy as np
import pytest
from numpy.typing import NDArray


def runtime() -> ModuleType:
    return import_module("labs.03_real_rag.end_to_end.runtime")


def test_dense_ranking_reaches_generator_and_acl_precedes_top_k() -> None:
    rt = runtime()
    chunks = rt.teacher_chunks()
    # The unauthorized nearest point must never enter the context or displace public evidence.
    vectors = np.array([[0.9, 0.1], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]])
    received: list[tuple[str, tuple[Any, ...]]] = []

    def provider(query: str, passages: tuple[Any, ...]) -> Any:
        received.append((query, passages))
        return rt.demo.Draft("300 dpi", (passages[0].chunk_id,))

    result = rt.run_case(
        rt.teacher_cases()[0], chunks, vectors, [1.0, 0.0], rt.Config(k=1, min_score=0.5), provider
    )
    assert result["retrieved_ids"] == [chunks[0].chunk_id]
    assert received[0][1][0].text == chunks[0].text
    assert result["answer"]["text"] == "300 dpi"
    assert result["retrieval"]["recall_at_k"] == 1
    assert result["answer_metrics"]["correct"] is True
    assert result["answer_metrics"]["supported"] is True


@pytest.mark.parametrize("kind", ["missing", "acl", "stale", "ambiguous"])
def test_policy_cases_do_not_call_provider(kind: str) -> None:
    rt = runtime()
    case = next(row for row in rt.teacher_cases() if row["kind"] == kind)

    def forbidden(*args: object) -> None:
        pytest.fail("policy must gate before provider")

    result = rt.run_case(
        case,
        rt.teacher_chunks(),
        [[1.0, 0.0]] * 4,
        [-1.0, 0.0] if kind == "missing" else [1.0, 0.0],
        rt.Config(k=2, min_score=0.5),
        forbidden,
    )
    assert result["answer"]["status"] == "no_answer"
    assert result["answer_metrics"]["abstention_correct"] is True


def test_relevant_retrieval_does_not_imply_correct_or_supported_answer() -> None:
    rt = runtime()
    result = rt.run_case(
        rt.teacher_cases()[0],
        rt.teacher_chunks(),
        [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]],
        [1.0, 0.0],
        rt.Config(k=1),
        lambda q, p: rt.demo.Draft("999 dpi", (p[0].chunk_id,)),
    )
    assert result["retrieval"]["recall_at_k"] == 1
    assert result["answer_metrics"]["correct"] is False
    assert result["answer_metrics"]["supported"] is False


def test_tuning_rejects_holdout_and_duplicate_queries() -> None:
    rt = runtime()
    rows = rt.teacher_cases()
    with pytest.raises(ValueError, match="dev"):
        rt.tune_threshold([rows[-1]], [0.1, 0.9], lambda case, threshold: 1.0)
    with pytest.raises(ValueError, match="unique"):
        rt.validate_cases([rows[0], rows[0]])


def test_evidence_rejects_author_and_missing_live_runs(tmp_path: Path) -> None:
    ev = import_module("labs.03_real_rag.end_to_end.evidence")
    with pytest.raises(ValueError, match="evidence"):
        ev.validate_submission(tmp_path)


def test_provider_outage_is_not_successful_abstention() -> None:
    rt = runtime()

    def unavailable(query: str, passages: tuple[Any, ...]) -> Any:
        raise rt.demo.ProviderUnavailable("offline")

    result = rt.run_case(
        rt.teacher_cases()[0],
        rt.teacher_chunks(),
        [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]],
        [1.0, 0.0],
        rt.Config(k=1),
        unavailable,
    )
    assert result["answer"]["status"] == "provider_error"
    assert result["answer_metrics"]["abstention_correct"] is False
    # Provider errors are reported separately, never counted as correct no-answer cases.
    absent = dict(rt.teacher_cases()[0], should_abstain=True, expected_answers=[])
    result = rt.run_case(
        absent,
        rt.teacher_chunks(),
        [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]],
        [1.0, 0.0],
        rt.Config(k=1),
        unavailable,
    )
    assert result["answer_metrics"]["abstention_correct"] is False


def test_live_runner_binds_encoder_queries_and_existing_provider_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rt = runtime()
    observed_texts: list[str] = []

    def encoder(
        directory: Path, texts: tuple[str, ...], *, pooling: str
    ) -> tuple[NDArray[np.float64], dict[str, str]]:
        observed_texts.extend(texts)
        assert pooling == "masked_mean"
        return np.array(
            [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]]
            + [
                [-1.0, 0.0] if "volcano" in row["query"].lower() else [1.0, 0.0]
                for row in rt.teacher_cases()
            ]
        ), {"pooling": "UNIT_FIXTURE_NOT_MODEL"}

    class Provider:
        last_prompt: str | None = None
        last_result = None

        def __call__(self, query: str, passages: tuple[Any, ...]) -> Any:
            self.last_prompt = "Unit fixture: " + query + passages[0].text
            return rt.demo.Draft("300 dpi", (passages[0].chunk_id,))

    def tags(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"models": [{"name": rt.local.MODEL, "digest": rt.local.MODEL_DIGEST}]}
        )

    original = httpx.Client
    monkeypatch.setattr(
        rt.httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(tags), **kw)
    )
    monkeypatch.setattr(rt.dense, "encode_local_minilm", encoder)
    monkeypatch.setattr(rt.local, "LocalGenerator", Provider)
    receipt = rt.run_live(tmp_path / "author", tmp_path)
    assert receipt["technical_status"] == "PASS"
    assert receipt["evidence_kind"] == "AUTHOR_LIVE_DENSE_RAG"
    assert observed_texts[:4] == [chunk.text for chunk in rt.teacher_chunks()]
    assert observed_texts[4:] == [row["query"] for row in rt.teacher_cases()]
    assert len(receipt["cases"]) == 10
    assert receipt["tuning"]["case_ids"] == [row["case_id"] for row in rt.teacher_cases()[:5]]
    assert all(row["prompt_sha256"] for row in receipt["cases"] if row["generator_called"])
    assert (tmp_path / "author" / "receipt.json").is_file()


def test_real_local_generator_consumes_dense_selected_passage() -> None:
    rt = runtime()

    def response(request: httpx.Request) -> httpx.Response:
        # Exercise existing Ollama/OpenAI SSE parser, not merely a provider-shaped mock.
        import json

        body = json.loads(request.content)
        prompt = body["messages"][0]["content"]
        assert "300 dpi" in prompt
        assert "STAFF-ONLY" not in prompt
        text = json.dumps({"text": "300 dpi", "citation_ids": ["A-SCAN@1:p1"]})
        chunk = {"choices": [{"delta": {"content": text}, "finish_reason": None}]}
        stop = {"choices": [{"delta": {}, "finish_reason": "stop"}]}
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text="data: "
            + json.dumps(chunk)
            + "\n\n"
            + "data: "
            + json.dumps(stop)
            + "\n\ndata: [DONE]\n\n",
        )

    provider = rt.local.LocalGenerator(transport=httpx.MockTransport(response))
    result = rt.run_case(
        rt.teacher_cases()[0],
        rt.teacher_chunks(),
        [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]],
        [1.0, 0.0],
        rt.Config(k=1),
        provider,
    )
    assert result["answer"]["status"] == "answer"
    assert result["stream"]["status"] == "ok"
    assert result["answer_metrics"]["correct"] is True


def test_dev_holdout_does_not_share_identical_queries() -> None:
    rt = runtime()
    first = rt.teacher_cases()[0]
    leaked = dict(first, case_id="leaked", split="holdout", query="  SCANNER resolution  ")
    with pytest.raises(ValueError, match="disjoint"):
        rt.validate_cases([first, leaked])


def test_summary_keeps_null_denominators_and_provider_failures_visible() -> None:
    rt = runtime()
    rows = []
    for case in rt.teacher_cases()[:2]:
        rows.append(
            rt.run_case(
                case,
                rt.teacher_chunks(),
                [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [0.0, 1.0]],
                [1.0, 0.0] if case["kind"] == "answerable" else [-1.0, 0.0],
                rt.Config(k=1),
                lambda q, p: rt.demo.Draft("wrong", (p[0].chunk_id,)),
            )
        )
    summary = rt.summarize(rows)["dev"]
    assert summary["cases"] == 2
    assert summary["recall_at_k"] == {"mean": 1.0, "denominator": 1}
    assert summary["correct"] == {"mean": 0.0, "denominator": 1}
    assert summary["abstention_correct"] == {"mean": 1.0, "denominator": 2}
    assert summary["provider_errors"] == 0
    assert summary["latency_p95_seconds"] >= summary["latency_p50_seconds"] >= 0


@pytest.fixture
def consistency_inputs(tmp_path: Path) -> Path:
    """Fabricated JSON for parser tests only; not an actual live/model experiment.

    The final human gate must rerun code; the read-only parser cannot authenticate JSON.
    No path is exported to ROADMAP_RAG_SUBMISSION or persisted as learner evidence.
    """
    import hashlib
    import json
    from dataclasses import asdict, dataclass

    rt = runtime()
    annotations = [dict(row, query=row["query"] + " please") for row in rt.teacher_cases()]
    model = rt.dense.import_module("labs.02_huggingface_models.download").resource_manifest()[
        "model"
    ]

    @dataclass
    class TestStream:
        status: str = "ok"

    class FixtureProvider:
        last_prompt: str | None = None
        last_result: TestStream | None = None

        def __call__(self, query: str, passages: tuple[Any, ...]) -> Any:
            self.last_prompt = "PARSER FIXTURE ONLY " + query
            self.last_result = TestStream()
            return rt.demo.Draft("300 dpi", (passages[0].chunk_id,))

    rows = [
        rt.run_case(
            row,
            rt.teacher_chunks(),
            [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [0.0, 1.0]],
            [-1.0, 0.0] if row["kind"] == "missing" else [1.0, 0.0],
            rt.Config(k=1),
            FixtureProvider(),
        )
        for row in annotations
    ]
    for name, pooling in (
        ("cls.json", "first-token-last-hidden-state-l2-v1"),
        ("masked_mean.json", "attention-mask-mean-last-hidden-state-l2-v1"),
    ):
        report = {
            "evidence_kind": "LEARNER_LIVE_DENSE_RAG",
            "technical_status": "PASS",
            "learner_source_sha256": hashlib.sha256(
                Path(str(rt.__file__)).with_name("starter.py").read_bytes()
            ).hexdigest(),
            "embedding": {
                "model": model["id"],
                "revision": model["revision"],
                "files": model["files"],
                "pooling": pooling,
            },
            "generator": {"model": rt.local.MODEL, "digest": rt.local.MODEL_DIGEST},
            "identity_unchanged": True,
            "annotations": annotations,
            "tuning": {"split": "dev", "case_ids": [r["case_id"] for r in annotations[:5]]},
            "config": asdict(rt.Config(k=1)),
            "config_sha256": rt.digest(asdict(rt.Config(k=1))),
            "queries_sha256": rt.digest(annotations),
            "corpus_sha256": rt.digest([asdict(c) for c in rt.teacher_chunks()]),
            "cases": rows,
        }
        (tmp_path / name).write_text(json.dumps(report), encoding="utf-8")
    review = {
        key: "Parser fixture only: observations require an independent human review."
        for key in (
            "hypothesis",
            "dev_selection",
            "retrieval_vs_answers",
            "failure_analysis",
            "uncertainty",
            "transfer",
            "human_support_review",
        )
    }
    (tmp_path / "review.json").write_text(
        json.dumps(dict(review, status="REQUIRES_REVIEW")), encoding="utf-8"
    )
    return tmp_path


def test_consistent_receipts_are_only_read_only_integrity_checks(consistency_inputs: Path) -> None:
    evidence = import_module("labs.03_real_rag.end_to_end.evidence")
    evidence.validate_submission(consistency_inputs)


@pytest.mark.parametrize("change", ["author", "model", "metrics", "prompt", "latency", "tuning"])
def test_evidence_cannot_ignore_incompatible_or_changed_results(
    consistency_inputs: Path, change: str
) -> None:
    import json

    evidence = import_module("labs.03_real_rag.end_to_end.evidence")
    path = consistency_inputs / "masked_mean.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if change == "author":
        report["evidence_kind"] = "AUTHOR_LIVE_DENSE_RAG"
    elif change == "model":
        report["embedding"]["revision"] = "other"
    elif change == "metrics":
        report["cases"][0]["retrieval"]["recall_at_k"] = 0.01
    elif change == "prompt":
        report["cases"][0]["prompt"] = "changed"
    elif change == "latency":
        report["cases"][0]["total_seconds"] = float("nan")
    else:
        report["tuning"]["case_ids"].append("holdout-answerable")
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="evidence"):
        evidence.validate_submission(consistency_inputs)


@pytest.mark.parametrize(
    "change",
    [
        "empty_retrieval",
        "score_shape",
        "score_string",
        "score_bool",
        "score_nan",
        "score_range",
        "below_cutoff",
        "too_many",
        "duplicate",
        "unknown",
        "private",
        "stale",
        "order",
        "tie_order",
        "context_budget",
        "context_selection",
        "provider_without_context",
        "invalid_config",
    ],
)
def test_evidence_binds_ranked_scores_budget_and_provider_context(
    consistency_inputs: Path, change: str
) -> None:
    import json

    rt = runtime()
    evidence = import_module("labs.03_real_rag.end_to_end.evidence")
    for name in ("cls.json", "masked_mean.json"):
        path = consistency_inputs / name
        report = json.loads(path.read_text(encoding="utf-8"))
        row = report["cases"][0]
        if change == "empty_retrieval":
            row["retrieved_ids"], row["scores"] = [], []
            row["retrieval"] = {"recall_at_k": 0.0, "reciprocal_rank": 0.0}
        elif change == "score_shape":
            row["scores"] = []
        elif change.startswith("score_"):
            row["scores"] = [
                {
                    "score_string": "not a cosine score",
                    "score_bool": True,
                    "score_nan": float("nan"),
                    "score_range": 1.1,
                }[change]
            ]
        elif change == "below_cutoff":
            row["scores"] = [report["config"]["min_score"] - 0.1]
        elif change in {"too_many", "order", "tie_order"}:
            row["retrieved_ids"] = ["A-SCAN@1:p1", "A-HOURS@1:p1"]
            row["scores"] = [0.8, 0.9] if change == "order" else [0.9, 0.9]
            if change != "too_many":
                report["config"]["k"] = 2
        elif change == "duplicate":
            row["retrieved_ids"] *= 2
            row["scores"] *= 2
            report["config"]["k"] = 2
        elif change in {"unknown", "private", "stale"}:
            item = {"unknown": "unknown", "private": "A-STAFF@1:p1", "stale": "A-SCAN@1:p1"}[change]
            row["retrieved_ids"] = [item]
            if change == "stale":
                report["annotations"][0]["stale_ids"] = [item]
                report["queries_sha256"] = rt.digest(report["annotations"])
        elif change == "context_budget":
            report["config"]["character_budget"] = 1
        elif change == "context_selection":
            row["context_ids"] = ["A-HOURS@1:p1"]
            row["answer"]["citation_ids"] = ["A-HOURS@1:p1"]
            row["answer_metrics"] = rt.answer_metrics(
                row["answer"], report["annotations"][0], (rt.teacher_chunks()[1],)
            )
        elif change == "provider_without_context":
            report["cases"][1]["generator_called"] = True
            report["cases"][1]["prompt"] = "a purported prompt"
            report["cases"][1]["prompt_sha256"] = rt.digest("a purported prompt")
        else:
            report["config"]["k"] = 0
        report["config_sha256"] = rt.digest(report["config"])
        path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="evidence"):
        evidence.validate_submission(consistency_inputs)


def test_evidence_accepts_structurally_consistent_zero_recall_and_unsupported_answer(
    consistency_inputs: Path,
) -> None:
    import json

    rt = runtime()
    evidence = import_module("labs.03_real_rag.end_to_end.evidence")
    for name in ("cls.json", "masked_mean.json"):
        path = consistency_inputs / name
        report = json.loads(path.read_text(encoding="utf-8"))
        row = report["cases"][0]
        row["retrieved_ids"] = row["context_ids"] = ["A-HOURS@1:p1"]
        row["scores"] = [0.8]
        row["retrieval"] = {"recall_at_k": 0.0, "reciprocal_rank": 0.0}
        row["answer"]["citation_ids"] = ["A-HOURS@1:p1"]
        row["answer_metrics"] = rt.answer_metrics(
            row["answer"], report["annotations"][0], (rt.teacher_chunks()[1],)
        )
        assert row["answer_metrics"]["supported"] is False
        path.write_text(json.dumps(report), encoding="utf-8")
    evidence.validate_submission(consistency_inputs)
