"""Two independent task axes compose, without a classifier granting retrieval permissions."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def test_teacher_composes_actual_classifier_and_bounded_extracts(tmp_path: Path) -> None:
    assert Path(__file__).parents[1].joinpath("integration_demo.py").is_file()
    module = importlib.import_module("projects.document_intelligence_lab.integration_demo")
    report = module.run_demo(tmp_path / "new")
    assert report["classification"]["predicted_label"] == "triangle"
    assert report["retrieval_cases"]["known"]["status"] == "answer"
    assert report["retrieval_cases"]["outage"]["status"] == "provider_error"
    assert report["retrieval_cases"]["deleted"]["status"] == "no_answer"
    assert report["retrieval_cases"]["private_only"]["status"] == "no_answer"
    assert report["retrieval_cases"]["no_source"]["status"] == "no_answer"
    assert report["answer_quality"] == "REQUIRES_REVIEW"
    assert report["llm_generation"] == "NOT_RUN"
    assert report["combined_ai_accuracy"] is None
    assert (tmp_path / "new" / "integration.json").is_file()
    with pytest.raises(FileExistsError):
        module.run_demo(tmp_path / "new")
