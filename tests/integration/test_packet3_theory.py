"""Verify teacher calculations, without grading student explanations or TODOs."""

from __future__ import annotations

import doctest
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = (
    "modules/03_data_foundations/04_practical_statistics/theory.md",
    "modules/04_machine_learning/07_training_bridge/theory.md",
)


@pytest.mark.parametrize("document", DOCUMENTS)
def test_independent_teacher_calculations(document: str, monkeypatch: pytest.MonkeyPatch) -> None:
    path = ROOT / document
    blocks = re.findall(r"^```pycon\n(.*?)\n```", path.read_text(encoding="utf-8"), re.M | re.S)
    assert blocks, f"No executable teacher transcripts in {path}"
    monkeypatch.chdir(ROOT)
    # Standalone pytest with importlib mode need not put the repository on sys.path.
    monkeypatch.syspath_prepend(ROOT)
    for number, source in enumerate(blocks, start=1):
        case = doctest.DocTestParser().get_doctest(source, {}, f"{document}:{number}", str(path), 0)
        result = doctest.DocTestRunner().run(case)
        assert result.attempted > 0
        assert result.failed == 0, f"Teacher calculation {number} disagrees with execution: {path}"
