"""A required external experiment: missing evidence is xfail health, strict failure."""

from pathlib import Path

import pytest

from projects.external_tabular.evidence import submission_or_incomplete
from roadmap_tools.exercise import exercise_call

from .protocol import validate_submission


@pytest.mark.student_exercise
def test_independent_external_pretrained_submission() -> None:
    root = Path(__file__).with_name("submission")
    exercise_call(submission_or_incomplete, root)
    assert validate_submission(root)["technical_status"] == "VERIFIED"
