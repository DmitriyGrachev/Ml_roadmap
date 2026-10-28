"""Execute teacher examples, independently of student exercise completion."""

from __future__ import annotations

import doctest
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LESSONS = (
    "modules/01_python_core/02_collections",
    "modules/01_python_core/03_functions",
    "modules/01_python_core/04_typing",
    "modules/03_data_foundations/01_numpy",
)


@pytest.mark.parametrize("lesson", LESSONS, ids=[path.rsplit("/", 1)[1] for path in LESSONS])
def test_published_interactive_examples(lesson: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Each pycon fence is a separate session with exact expected results."""
    path = ROOT / lesson / "theory.md"
    examples = re.findall(r"^```pycon\n(.*?)\n```", path.read_text(encoding="utf-8"), re.M | re.S)
    assert examples, f"No executable teacher examples found in {path}"
    monkeypatch.chdir(ROOT)
    runner = doctest.DocTestRunner()
    for number, source in enumerate(examples, start=1):
        case = doctest.DocTestParser().get_doctest(source, {}, f"{lesson}:{number}", str(path), 0)
        result = runner.run(case)
        assert result.attempted > 0
        assert result.failed == 0, f"Published example {number} differs from execution in {path}"
