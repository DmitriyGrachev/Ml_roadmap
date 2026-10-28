"""Execute independent teacher transcripts, not a text-answer grading system."""

from __future__ import annotations

import doctest
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LESSONS = (
    "01_problem_framing",
    "02_validation",
    "03_preprocessing",
    "04_models",
    "05_evaluation",
    "06_reproducibility",
)


@pytest.mark.parametrize("lesson", LESSONS)
def test_teacher_transcripts_are_independent(lesson: str, monkeypatch: pytest.MonkeyPatch) -> None:
    path = ROOT / "modules/04_machine_learning" / lesson / "theory.md"
    monkeypatch.chdir(ROOT)
    monkeypatch.syspath_prepend(ROOT)
    for number, code in enumerate(
        re.findall(r"^```pycon\n(.*?)\n```", path.read_text(encoding="utf-8"), re.M | re.S)
    ):
        case = doctest.DocTestParser().get_doctest(code, {}, f"{lesson}:{number}", str(path), 0)
        result = doctest.DocTestRunner().run(case)
        assert result.attempted > 0
        assert result.failed == 0, f"Teacher calculation disagrees with code: {lesson}:{number}"
