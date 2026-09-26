"""Manually reviewed answer support is distinct from retrieval success."""

from importlib import import_module

import pytest

example = import_module("modules.06_rag.06_rag_evaluation.example")


def test_outcomes_keep_retrieval_and_generation_failures_separate() -> None:
    assert example.failure_counts() == {
        "answer_failure": 1,
        "correct_abstention": 1,
        "retrieval_miss": 1,
        "supported_answer": 1,
    }


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
