"""Run each published packet-two teacher transcript in a fresh namespace."""

from __future__ import annotations

import doctest
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTS = (
    "02_pandas_core/theory.md",
    "03_data_quality/theory.md",
    "03_data_quality/eda.md",
)


@pytest.mark.parametrize("document", DOCUMENTS)
def test_independent_teacher_transcripts(document: str, monkeypatch: pytest.MonkeyPatch) -> None:
    path = ROOT / "modules/03_data_foundations" / document
    blocks = re.findall(r"^```pycon\n(.*?)\n```", path.read_text(encoding="utf-8"), re.M | re.S)
    assert blocks, f"No executable transcripts in {path}"
    monkeypatch.chdir(ROOT)
    for number, source in enumerate(blocks, start=1):
        case = doctest.DocTestParser().get_doctest(source, {}, f"{document}:{number}", str(path), 0)
        result = doctest.DocTestRunner().run(case)
        assert result.attempted > 0
        assert result.failed == 0, f"Transcript {number} disagrees with execution: {path}"
