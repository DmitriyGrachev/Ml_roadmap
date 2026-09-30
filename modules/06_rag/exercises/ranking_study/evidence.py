"""Read saved ranking evidence; compose existing student metrics without replacing them."""

import argparse
import hashlib
import importlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from roadmap_tools.experiment_evidence import checked_artifact, validate_identity
from roadmap_tools.open_control_evidence import ids, object_value, read_json, require

evaluation = importlib.import_module(
    "modules.06_rag.06_rag_evaluation.exercises.retrieval_evaluation.starter"
)
regression = importlib.import_module("modules.06_rag.exercises.retrieval_regression.starter")
FIXTURES = Path(__file__).parent / "fixtures"


def validate_split(split: dict[str, Any], queries: list[dict[str, Any]]) -> list[str]:
    train, test = ids(split.get("train_ids")), ids(split.get("test_ids"))
    by_id = {row["id"]: row for row in queries}
    require(not set(train) & set(test) and set(train + test) == set(by_id), "query IDs differ")
    require(
        not {by_id[x]["group"] for x in train} & {by_id[x]["group"] for x in test},
        "semantic groups overlap",
    )
    return test


def authorized_run(
    raw: Any, documents: list[dict[str, Any]], roles: list[str], k: int
) -> list[str]:
    require(type(k) is int and k > 0, "positive integer k required")
    by_id = {row["id"]: row for row in documents}
    require(isinstance(raw, list) and all(isinstance(x, str) for x in raw), "document IDs")
    require(len(raw) == len(set(raw)) and set(raw) <= by_id.keys(), "document IDs")
    return [key for key in raw if set(roles) & set(by_id[key]["roles"])][:k]


def recompute(judgments: dict[str, Any], runs: dict[str, Any], k: int) -> dict[str, Any]:
    """No fallback: unfinished prerequisite metrics raise NotImplementedError."""
    require(len(runs) == 2, "exactly two methods required")
    names = list(runs)
    metrics = {
        name: asdict(evaluation.evaluate_retrieval(judgments, runs[name], k=k)) for name in names
    }
    binary = tuple(
        regression.QueryJudgment(
            query, frozenset(doc for doc, grade in grades.items() if grade > 0)
        )
        for query, grades in sorted(judgments.items())
    )
    paired = regression.compare_retrieval(
        binary,
        {q: tuple(v) for q, v in runs[names[0]].items()},
        {q: tuple(v) for q, v in runs[names[1]].items()},
        k=k,
    )
    return dict(json.loads(json.dumps({"methods": metrics, "comparison": asdict(paired)})))


def validate_evidence(root: Path) -> None:
    manifest = object_value(read_json(root / "manifest.json"))
    artifacts = object_value(manifest.get("artifacts"))
    required = {
        "corpus.jsonl",
        "queries.jsonl",
        "judgments.json",
        "split.json",
        "outputs.json",
        "implementation.txt",
        "report.md",
    }
    require(required <= artifacts.keys(), "missing artifacts")
    for name, digest in artifacts.items():
        path = checked_artifact(root, name, digest)
        require(bool(path.read_bytes().strip()), "empty artifact")
        if name in {"corpus.jsonl", "queries.jsonl", "judgments.json"}:
            require(
                path.read_bytes() == (FIXTURES / name).read_bytes(), "stale fixture or judgments"
            )
    validate_identity(
        manifest,
        exercise_id="rag-ranking-study",
        dataset_sha256=hashlib.sha256((FIXTURES / "corpus.jsonl").read_bytes()).hexdigest(),
        split_sha256=artifacts["split.json"],
    )
    require(isinstance(manifest.get("run_id"), str) and manifest["run_id"].strip(), "run ID")
    require(manifest.get("review_status") == "REQUIRES_REVIEW", "manual review required")
    documents = [json.loads(line) for line in (root / "corpus.jsonl").read_text().splitlines()]
    queries = [json.loads(line) for line in (root / "queries.jsonl").read_text().splitlines()]
    test = validate_split(object_value(read_json(root / "split.json")), queries)
    outputs = object_value(read_json(root / "outputs.json"))
    for key in ("run_id", "dataset_sha256", "split_sha256"):
        require(outputs.get(key) == manifest[key], "output identity differs")
    k = manifest["config"].get("k")
    require(type(k) is int and k > 0, "positive integer k required")
    methods = object_value(outputs.get("methods"))
    require(
        len(methods) == 2 and all(isinstance(x, str) and x.strip() for x in methods),
        "exactly two named methods required",
    )
    query_map = {row["id"]: row for row in queries}
    runs = {}
    for name, method in methods.items():
        method = object_value(method)
        raw = object_value(method.get("rankings"))
        saved = object_value(method.get("runs"))
        require(set(raw) == set(saved) == set(test), "held-out query IDs differ")
        expected = {q: authorized_run(raw[q], documents, query_map[q]["roles"], k) for q in test}
        require(saved == expected, "access before cutoff or saved run differs")
        runs[name] = saved
    judgments = object_value(read_json(root / "judgments.json"))
    actual = recompute({q: judgments[q] for q in test}, runs, k)
    require(
        json.dumps(outputs.get("metrics"), sort_keys=True, allow_nan=False)
        == json.dumps(actual, sort_keys=True, allow_nan=False),
        "recomputed metrics differ",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read saved ranking artifacts")
    parser.add_argument("root", type=Path)
    validate_evidence(parser.parse_args().root)
    print("Consistency checked; method execution and interpretation REQUIRES_REVIEW")
