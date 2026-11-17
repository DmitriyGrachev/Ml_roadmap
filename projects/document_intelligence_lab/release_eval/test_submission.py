from pathlib import Path

import pytest

from roadmap_tools.exercise import exercise_call

from .review import validate_submission


@pytest.mark.student_exercise
def test_independent_release_decision() -> None:
    root = Path(__file__).resolve().parents[3]
    exercise_call(validate_submission, root / "generated-reports/release-eval/submission")
