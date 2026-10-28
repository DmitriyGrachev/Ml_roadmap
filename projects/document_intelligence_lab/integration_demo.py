"""Compose existing teacher modules once; no agent loop, LLM, or student solution."""

from __future__ import annotations

import argparse
import importlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .artifacts import file_sha256, json_bytes
from .part_a1.demo import run_demo as run_a1
from .service.app import create_app


def run_demo(output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(output)
    from fastapi.testclient import TestClient

    rag = importlib.import_module("labs.03_real_rag.demo")
    runs = run_a1(output / "classification")
    bundle = runs / "tfidf-linear"
    app = create_app(
        bundle, file_sha256(bundle / "manifest.json"), trusted_local_artifact=True
    )  # Only the teacher-owned bytes just written, never a caller-supplied pickle.
    with TestClient(app) as client:
        response = client.post("/predict", json={"text": "small blue triangle"})
        response.raise_for_status()
        classification = response.json()

    sources = rag.teacher_sources()

    def unavailable(query: str, passages: tuple[Any, ...]) -> Any:
        raise rag.ProviderUnavailable("intentional teacher outage")

    # Access policy is fixed by the operator. Neither the model label nor a query
    # can grant staff permissions. Each case calls its provider at most once.
    cases = {
        "known": rag.answer_query("scanner settings", sources),
        "outage": rag.answer_query("scanner settings", sources, generator=unavailable),
        "deleted": rag.answer_query("scanner settings", sources, current_sources=()),
        "private_only": rag.answer_query("cabinet code", sources),
        "no_source": rag.answer_query("volcano insurance", sources),
    }
    report = {
        "evidence_kind": "AUTHOR_COMPOSITION_CLASSIFIER_AND_EXTRACTS",
        "classification": classification,
        "classification_evaluation": "classification/comparison.json: separate fixed test cohort",
        "retrieval_cases": {name: asdict(answer) for name, answer in cases.items()},
        "answer_quality": "REQUIRES_REVIEW",
        "llm_generation": "NOT_RUN",
        "qdrant": "NOT_RUN",
        "vllm": "NOT_RUN",
        "combined_ai_accuracy": None,
        "limits": {
            "cases": 5,
            "provider_calls_per_case": 1,
            "retries": 0,
            "context_characters": 2000,
            "top_k": 2,
        },
    }
    (output / "integration.json").write_bytes(json_bytes(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run_demo(args.output)
    print(args.output / "integration.json")
