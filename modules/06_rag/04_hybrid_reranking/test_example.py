"""Reranking cannot recover documents outside its candidate shortlist."""

from importlib import import_module

import pytest

example = import_module("modules.06_rag.04_hybrid_reranking.example")


def test_reranking_has_a_candidate_ceiling_and_stable_ties() -> None:
    shortlist = ["b", "a", "c"]
    scores = {"a": 0.7, "b": 0.7, "c": 0.2, "missing": 1.0}
    assert example.rerank_shortlist(shortlist, scores) == ("a", "b", "c")
    assert shortlist == ["b", "a", "c"]
    assert example.rerank_shortlist([], scores) == ()


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
