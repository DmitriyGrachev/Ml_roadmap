"""Author input/evidence safety checks, excluded from learner completion."""

import hashlib
import json
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

rt = import_module("labs.03_real_rag.neural_reranking.runtime")


def cases() -> dict[str, Any]:
    return {
        "corpus": [{"id": "a", "text": "Alpha"}, {"id": "b", "text": "Beta"}],
        "queries": [
            {"query_id": "d", "query": "dev?", "split": "dev", "candidate_ids": ["a"]},
            {"query_id": "h", "query": "test?", "split": "holdout", "candidate_ids": ["b"]},
        ],
        "qrels": {"d": {"a": 2}, "h": {"a": 1}},
    }


def test_accepts_relevant_document_outside_candidate_pool() -> None:
    rt.validate_cases(cases())


@pytest.mark.parametrize("change", ["query_id", "query", "candidate", "qrels", "grade"])
def test_input_isolation_and_identity(change: str) -> None:
    data = cases()
    if change in {"query_id", "query"}:
        data["queries"][1][change] = data["queries"][0][change]
    elif change == "candidate":
        data["queries"][0]["candidate_ids"] = ["missing"]
    elif change == "qrels":
        data["qrels"]["unrelated"] = {}
    else:
        data["qrels"]["d"]["a"] = -1
    with pytest.raises(ValueError):  # noqa: PT011
        rt.validate_cases(data)


def test_model_path_never_resolves_remote_identifier(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="local"):
        rt.local_scorer(tmp_path / "missing")


def test_missing_or_author_evidence_cannot_complete(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="evidence"):
        rt.validate_submission(tmp_path)


@pytest.fixture
def parser_fixture(tmp_path: Path) -> Path:
    """Fabricated parser input only; never exported as learner evidence or run receipt."""
    metrics = {
        "d": {"candidate_recall": 1.0, "mrr_at_k": 1.0, "ndcg_at_k": 1.0},
        "h": {"candidate_recall": 0.0, "mrr_at_k": 0.0, "ndcg_at_k": 0.0},
    }
    report = {
        "evidence_kind": "LEARNER_LOCAL_PRETRAINED_RERANKING",
        "status": "PASS",
        "quality": "REQUIRES_REVIEW",
        "learner_source_sha256": hashlib.sha256(
            Path(str(rt.__file__)).with_name("starter.py").read_bytes()
        ).hexdigest(),
        "provenance": {
            "kind": "pretrained",
            "model_id": "PARSER_FIXTURE_ONLY",
            "revision": "NOT_REAL",
            "license": "fixture",
        },
        "snapshot": {"config.json": "0" * 64},
        "data": cases(),
        "k": 1,
        "rows": [
            {
                "query_id": "d",
                "ranking": [{"id": "a", "text": "Alpha", "score": 0.5}],
                "seconds": 0.1,
            },
            {
                "query_id": "h",
                "ranking": [{"id": "b", "text": "Beta", "score": 0.2}],
                "seconds": 0.1,
            },
        ],
        "metrics": metrics,
        "baseline_metrics": metrics,
    }
    (tmp_path / "report.json").write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "review.json").write_text(
        json.dumps(
            {
                "status": "REQUIRES_REVIEW",
                **{
                    key: "Fabricated parser fixture only. Does not establish an actual model run."
                    for key in (
                        "candidate_ceiling",
                        "failure_analysis",
                        "cost",
                        "transfer",
                        "provenance_review",
                    )
                },
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_consistency_parser_is_not_proof_of_execution(parser_fixture: Path) -> None:
    rt.validate_submission(parser_fixture)


@pytest.mark.parametrize(
    "change", ["author", "id", "score", "metric", "baseline", "query_id", "source"]
)
def test_submission_tampering_rejected(parser_fixture: Path, change: str) -> None:
    path = parser_fixture / "report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if change == "author":
        report["evidence_kind"] = "AUTHOR_RANDOM_API_SMOKE"
    elif change == "id":
        report["rows"][1]["ranking"][0]["id"] = "a"
    elif change == "score":
        report["rows"][0]["ranking"][0]["score"] = float("nan")
    elif change == "metric":
        report["metrics"]["h"]["candidate_recall"] = 0.5
    elif change == "baseline":
        report["baseline_metrics"]["d"]["ndcg_at_k"] = 0.5
    elif change == "query_id":
        report["rows"][1]["query_id"] = "d"
    else:
        report["learner_source_sha256"] = "changed"
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="evidence"):
        rt.validate_submission(parser_fixture)
