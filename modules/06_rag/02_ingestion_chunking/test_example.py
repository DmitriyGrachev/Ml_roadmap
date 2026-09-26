"""Source lifecycle plans detect changes, policy revisions and deletions."""

from importlib import import_module

import pytest

example = import_module("modules.06_rag.02_ingestion_chunking.example")


def test_plan_is_idempotent_and_marks_deleted_sources() -> None:
    previous = {"a": "old", "b": "same", "removed": "old"}
    current = {"a": "new", "b": "same", "added": "new"}
    assert example.update_plan(previous, current) == {
        "unchanged": ("b",),
        "replace": ("a", "added"),
        "tombstone": ("removed",),
    }
    assert example.update_plan(current, current) == {
        "unchanged": ("a", "added", "b"),
        "replace": (),
        "tombstone": (),
    }
    assert previous == {"a": "old", "b": "same", "removed": "old"}


def test_digest_changes_when_text_or_extraction_policy_changes() -> None:
    first = example.source_digest("Water weekly.")
    assert first == example.source_digest("Water weekly.")
    assert first != example.source_digest("Water daily.")
    assert first != example.source_digest("Water weekly.", "plain-text-v2")


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
