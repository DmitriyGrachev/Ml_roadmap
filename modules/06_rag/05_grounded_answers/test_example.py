"""Context packing preserves structured source identity and exposes abstention."""

import json
from importlib import import_module

import pytest

example = import_module("modules.06_rag.05_grounded_answers.example")


def test_packing_counts_serialization_overhead_and_preserves_identifiers() -> None:
    passage = example.ContextPassage("a:r1:0", "a", "Shade helps herbs.")
    state, content = example.pack_context([passage], 200)
    assert state == "evidence_available"
    assert len(content) <= 200
    assert json.loads(content) == [
        {"chunk_id": "a:r1:0", "source_id": "a", "text": "Shade helps herbs."}
    ]
    assert example.pack_context([passage], len(content))[0] == "evidence_available"
    assert example.pack_context([passage], len(content) - 1) == ("insufficient_evidence", "[]")


def test_empty_or_too_small_context_is_explicit() -> None:
    assert example.pack_context([], 2) == ("insufficient_evidence", "[]")
    with pytest.raises(ValueError, match="character_budget"):
        example.pack_context([], 1)


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
