"""Lexical vocabulary and synthetic geometry remain separate demonstrations."""

from importlib import import_module

import pytest

example = import_module("modules.06_rag.03_lexical_dense_retrieval.example")


def test_lexical_query_has_a_clear_match_and_unknown_terms_have_zero_scores() -> None:
    scores = example.lexical_scores("library maps")
    assert scores[0] > 0
    assert scores[1:] == (0.0, 0.0)
    assert example.lexical_scores("volcano") == (0.0, 0.0, 0.0)


def test_cosine_ignores_positive_scale_in_hand_supplied_vectors() -> None:
    assert example.synthetic_geometry() == pytest.approx(1.0)


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
