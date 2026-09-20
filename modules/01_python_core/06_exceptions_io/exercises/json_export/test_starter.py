"""Acceptance tests for atomic JSON export."""

import json
import os
from pathlib import Path
from typing import NoReturn

import pytest

from roadmap_tools import exercise_call

from .starter import export_json_atomic


@pytest.mark.student_exercise
def test_export_writes_json_atomically_and_returns_the_destination(tmp_path: Path) -> None:
    destination = tmp_path / "report.json"
    payload = {"transaction": "txn-1", "amount": "12.50"}

    result = exercise_call(export_json_atomic, payload, destination)

    assert result == destination
    assert json.loads(destination.read_text(encoding="utf-8")) == payload
    assert set(tmp_path.iterdir()) == {destination}


@pytest.mark.student_exercise
def test_export_writes_unicode_as_utf8_text(tmp_path: Path) -> None:
    destination = tmp_path / "report.json"

    exercise_call(export_json_atomic, {"merchant": "Café Chișinău"}, destination)

    assert "Café Chișinău" in destination.read_text(encoding="utf-8")


@pytest.mark.student_exercise
def test_serialization_failure_preserves_destination_and_removes_temporary_file(
    tmp_path: Path,
) -> None:
    class Unserializable:
        pass

    destination = tmp_path / "report.json"
    destination.write_text('{"state":"original"}', encoding="utf-8")
    unrelated = tmp_path / "keep.tmp"
    unrelated.write_text("owned by another operation", encoding="utf-8")
    original_entries = set(tmp_path.iterdir())

    with pytest.raises(TypeError) as caught:
        exercise_call(export_json_atomic, {"value": Unserializable()}, destination)

    assert caught.value.args == ("Object of type Unserializable is not JSON serializable",)
    assert destination.read_text(encoding="utf-8") == '{"state":"original"}'
    assert set(tmp_path.iterdir()) == original_entries


@pytest.mark.student_exercise
def test_replacement_failure_preserves_destination_and_removes_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "report.json"
    destination.write_text('{"state":"original"}', encoding="utf-8")
    unrelated = tmp_path / "keep.tmp"
    unrelated.write_text("owned by another operation", encoding="utf-8")
    original_entries = set(tmp_path.iterdir())
    replacement_error = OSError("replacement blocked")

    def fail_replacement(_source: object, _target: object) -> NoReturn:
        raise replacement_error

    monkeypatch.setattr(os, "replace", fail_replacement)

    with pytest.raises(OSError, match="replacement blocked") as caught:
        exercise_call(export_json_atomic, {"state": "new"}, destination)

    assert caught.value is replacement_error
    assert destination.read_text(encoding="utf-8") == '{"state":"original"}'
    assert set(tmp_path.iterdir()) == original_entries
