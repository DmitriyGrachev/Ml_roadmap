"""Assessed learner boundary: only an untouched NotImplementedError may xfail."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from roadmap_tools import exercise_call

from ...artifacts import read_json
from .protocol import FIXTURES, validate_reproduction
from .starter import run_reproduction


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> None:
        raise AssertionError("exercise must remain offline")

    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)


@pytest.mark.student_exercise
def test_independent_reproduction_survives_fresh_process_and_relocation(tmp_path: Path) -> None:
    output = tmp_path / "original"
    result = exercise_call(run_reproduction, FIXTURES, output, seed=23)
    assert result == output
    assert (
        validate_reproduction(output, trusted_local_artifact=True)["mechanical_status"]
        == "VERIFIED"
    )
    moved = tmp_path / "relocated"
    shutil.move(str(output), moved)
    script = """import json,sys
from pathlib import Path
from projects.document_intelligence_lab.part_a1.exercise.protocol import validate_reproduction
print(json.dumps(validate_reproduction(Path(sys.argv[1]),trusted_local_artifact=True)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, str(moved)], capture_output=True, text=True, check=True
    )
    assert json.loads(completed.stdout)["mechanical_status"] == "VERIFIED"


@pytest.mark.student_exercise
def test_repeated_run_preserves_old_bytes_and_same_predictions(tmp_path: Path) -> None:
    first = tmp_path / "first"
    exercise_call(run_reproduction, FIXTURES, first, seed=23)
    before = {
        path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()
    }
    with pytest.raises(FileExistsError):
        run_reproduction(FIXTURES, first, seed=23)
    assert before == {
        path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()
    }
    second = tmp_path / "second"
    run_reproduction(FIXTURES, second, seed=23)
    for output in (first, second):
        validate_reproduction(output, trusted_local_artifact=True)
    for method in ("rules", "tfidf-linear"):
        assert read_json(first / method / "predictions.json") == read_json(
            second / method / "predictions.json"
        )
