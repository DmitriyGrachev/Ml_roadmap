"""Student results must include actual prediction evidence."""

from pathlib import Path

import pytest

from roadmap_tools.exercise import exercise_call

from .evidence import validate_evidence
from .starter import investigate

pytestmark = pytest.mark.student_exercise


def test_investigation_returns_verifiable_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "investigation"
    manifest = exercise_call(investigate, output)
    assert manifest.resolve() == (output / "manifest.json").resolve()
    validate_evidence(output)


def test_investigation_preserves_existing_work(tmp_path: Path) -> None:
    marker = tmp_path / "notes.txt"
    marker.write_text("existing learner work")
    with pytest.raises(FileExistsError):
        exercise_call(investigate, tmp_path)
    assert marker.read_text() == "existing learner work"
