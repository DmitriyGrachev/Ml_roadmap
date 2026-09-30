"""Infrastructure checks; constant dependency spies are NOT retrieval solutions."""

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


def test_missing_artifacts_fail(tmp_path: Path) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    with pytest.raises(ValueError, match="invalid JSON"):
        module.validate_evidence(tmp_path)


def test_access_is_applied_before_cutoff() -> None:
    module = importlib.import_module(__package__ + ".evidence")
    documents = [{"id": "secret", "roles": ["admin"]}, {"id": "public", "roles": ["user"]}]
    assert module.authorized_run(["secret", "public"], documents, ["user"], 1) == ["public"]
    assert module.authorized_run(["public"], documents, [], 1) == []
    with pytest.raises(ValueError, match="document IDs"):
        module.authorized_run(["public", "unknown"], documents, ["user"], 1)
    with pytest.raises(ValueError, match="document IDs"):
        module.authorized_run(["public", "public"], documents, ["user"], 1)


@pytest.mark.parametrize("test", [["b"], ["c", "c"], ["foreign"], []])
def test_split_rejects_group_leakage_and_unknown_ids(test: list[str]) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    queries = [
        {"id": "a", "group": "same"},
        {"id": "b", "group": "same"},
        {"id": "c", "group": "other"},
    ]
    with pytest.raises(ValueError, match=r"query IDs|groups overlap|duplicate IDs|nonempty ID"):
        module.validate_split({"train_ids": ["a", "c"], "test_ids": test}, queries)


def test_metrics_compose_existing_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    calls: list[str] = []

    def evaluate(judgments: Any, results: Any, *, k: int) -> Any:
        assert judgments == {"q": {"d": 3}}
        assert results == {"q": ["d"]}
        assert k == 1
        calls.append("graded")
        return module.evaluation.RetrievalEvaluation(
            (module.evaluation.QueryMetrics("q", 1, 1, 1.0, 1.0, 1.0),), 1.0, 1.0, 1.0
        )

    def compare(judgments: Any, baseline: Any, candidate: Any, **kwargs: Any) -> Any:
        assert judgments == (module.regression.QueryJudgment("q", frozenset({"d"})),)
        assert baseline == candidate == {"q": ("d",)}
        assert kwargs == {"k": 1}
        calls.append("paired")
        return module.regression.RegressionReport(1, 1.0, 1.0, (), True)

    monkeypatch.setattr(module.evaluation, "evaluate_retrieval", evaluate)
    monkeypatch.setattr(module.regression, "compare_retrieval", compare)
    result = module.recompute({"q": {"d": 3}}, {"left": {"q": ["d"]}, "right": {"q": ["d"]}}, 1)
    assert result["methods"]["left"]["mean_ndcg_at_k"] == 1.0
    assert result["comparison"]["query_count"] == 1
    assert calls == ["graded", "graded", "paired"]


def ranking_bundle(root: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Two fixed, perfect one-hit rows; spies do no ranking or metric computation."""
    module = importlib.import_module(__package__ + ".evidence")
    query_ids = ["q-hours", "q-contact"]
    rows = [
        {
            "query_id": q,
            "relevant_total": 1,
            "retrieved_count": 1,
            "recall_at_k": 1.0,
            "reciprocal_rank": 1.0,
            "ndcg_at_k": 1.0,
        }
        for q in sorted(query_ids)
    ]
    evaluated = {"per_query": rows, "mean_recall_at_k": 1.0, "mrr_at_k": 1.0, "mean_ndcg_at_k": 1.0}

    def evaluate(judgments: Any, results: Any, *, k: int) -> Any:
        assert judgments == {"q-hours": {"d-hours": 3}, "q-contact": {"d-hours": 2}}
        assert results == {q: ["d-hours"] for q in query_ids}
        assert k == 1
        return module.evaluation.RetrievalEvaluation(
            tuple(module.evaluation.QueryMetrics(**row) for row in rows), 1.0, 1.0, 1.0
        )

    def compare(judgments: Any, baseline: Any, candidate: Any, *, k: int) -> Any:
        assert tuple(x.query_id for x in judgments) == ("q-contact", "q-hours")
        assert baseline == candidate == {q: ("d-hours",) for q in query_ids}
        assert k == 1
        return module.regression.RegressionReport(2, 1.0, 1.0, (), True)

    monkeypatch.setattr(module.evaluation, "evaluate_retrieval", evaluate)
    monkeypatch.setattr(module.regression, "compare_retrieval", compare)
    for name in ("corpus.jsonl", "queries.jsonl", "judgments.json"):
        (root / name).write_bytes((module.FIXTURES / name).read_bytes())
    (root / "split.json").write_text(
        json.dumps(
            {"train_ids": ["q-reset", "q-recover", "q-return", "q-bill"], "test_ids": query_ids}
        )
    )
    artifacts = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in ("corpus.jsonl", "queries.jsonl", "judgments.json", "split.json")
    }
    identity = {
        "run_id": "test-only",
        "dataset_sha256": artifacts["corpus.jsonl"],
        "split_sha256": artifacts["split.json"],
    }
    output = {
        **identity,
        "methods": {
            name: {
                "rankings": {q: ["d-admin", "d-hours", "d-account"] for q in query_ids},
                "runs": {q: ["d-hours"] for q in query_ids},
            }
            for name in ("left", "right")
        },
        "metrics": {
            "methods": {"left": evaluated, "right": evaluated},
            "comparison": {
                "query_count": 2,
                "baseline_mean": 1.0,
                "candidate_mean": 1.0,
                "regressed_queries": [],
                "passed": True,
            },
        },
    }
    (root / "outputs.json").write_text(json.dumps(output))
    (root / "implementation.txt").write_text(
        "TEST ONLY; fixed dependency spies, no learner solution"
    )
    (root / "report.md").write_text("TEST ONLY; no model execution provenance")
    manifest = {
        **identity,
        "schema_version": 1,
        "exercise_id": "rag-ranking-study",
        "config": {"k": 1},
        "review_status": "REQUIRES_REVIEW",
        "artifacts": artifacts,
    }
    refresh_bundle(root, manifest)
    return manifest


def refresh_bundle(root: Path, manifest: dict[str, Any]) -> None:
    for path in root.iterdir():
        if path.name != "manifest.json":
            manifest["artifacts"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (root / "manifest.json").write_text(json.dumps(manifest))


@pytest.mark.parametrize(
    "change",
    [
        None,
        "identity",
        "unknown",
        "access",
        "query",
        "judgments",
        "metric",
        "metric_bool",
        "split",
        "bytes",
    ],
)
def test_saved_ranking_bundle_rejects_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str | None
) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    manifest = ranking_bundle(tmp_path, monkeypatch)
    output = json.loads((tmp_path / "outputs.json").read_text())
    if change == "identity":
        output["run_id"] = "foreign"
    elif change == "unknown":
        output["methods"]["left"]["rankings"]["q-hours"].append("foreign")
    elif change == "access":
        output["methods"]["left"]["runs"]["q-hours"] = []
    elif change == "query":
        output["methods"]["left"]["runs"]["foreign"] = []
    elif change == "metric":
        output["metrics"]["comparison"]["candidate_mean"] = 0.5
    elif change == "metric_bool":
        output["metrics"]["methods"]["left"]["mrr_at_k"] = True
    elif change == "judgments":
        (tmp_path / "judgments.json").write_text('{"q-hours":{"d-hours":0}}')
    elif change == "split":
        (tmp_path / "split.json").write_text('{"train_ids":["q-hours"],"test_ids":["q-contact"]}')
    (tmp_path / "outputs.json").write_text(json.dumps(output))
    refresh_bundle(tmp_path, manifest)
    if change == "bytes":
        (tmp_path / "report.md").write_text("changed bytes")
    if change is None:
        module.validate_evidence(tmp_path)
    else:
        with pytest.raises(ValueError, match=r"differ|IDs|stale|does not match"):
            module.validate_evidence(tmp_path)
