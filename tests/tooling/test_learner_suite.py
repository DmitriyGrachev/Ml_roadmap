"""Solving a learner task must not trigger the untouched-template policy."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_solved_work_passes_default_suite_but_fails_explicit_template_gate(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    (tmp_path / "conftest.py").write_bytes((root / "conftest.py").read_bytes())
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    maintainer_only: untouched templates\n", encoding="utf-8"
    )
    (tmp_path / "test_work.py").write_text(
        "import pytest\n"
        "def answer():\n    return 42\n"
        "def test_learner_result():\n    assert answer() == 42\n"
        "@pytest.mark.maintainer_only\n"
        "def test_distributed_template():\n"
        "    with pytest.raises(NotImplementedError):\n        answer()\n",
        encoding="utf-8",
    )
    command = [sys.executable, "-m", "pytest", "-q", str(tmp_path)]
    learner = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, check=False)
    assert learner.returncode == 0, learner.stdout + learner.stderr
    assert "1 passed, 1 deselected" in learner.stdout
    maintainer = subprocess.run(
        [*command, "--maintainer", "-m", "maintainer_only"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert maintainer.returncode == 1
    assert "DID NOT RAISE" in maintainer.stdout
