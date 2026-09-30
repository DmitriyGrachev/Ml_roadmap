"""Student routing needs real output records and resource accounting."""

from pathlib import Path

import pytest

from roadmap_tools.exercise import exercise_call

from .evidence import FIXTURES, validate_evidence
from .starter import run_study

pytestmark = pytest.mark.student_exercise


def test_study_returns_verifiable_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "study"
    manifest = exercise_call(run_study, FIXTURES, output)
    assert manifest.resolve() == (output / "manifest.json").resolve()
    validate_evidence(output)


def test_study_preserves_existing_work(tmp_path: Path) -> None:
    marker = tmp_path / "notes.txt"
    marker.write_text("existing learner work")
    with pytest.raises(FileExistsError):
        exercise_call(run_study, FIXTURES, tmp_path)
    assert marker.read_text() == "existing learner work"
