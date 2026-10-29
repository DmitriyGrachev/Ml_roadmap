"""The catalog strict gate selects this file; maintainer fixture tests grant no credit."""

from pathlib import Path

import pytest

from roadmap_tools.exercise import exercise_call

from .evidence import submission_or_incomplete
from .protocol import validate_submission


@pytest.mark.student_exercise
def test_independent_external_tabular_submission() -> None:
    root = Path(__file__).with_name("submission")
    exercise_call(submission_or_incomplete, root)
    assert validate_submission(root)["technical_status"] == "VERIFIED"
