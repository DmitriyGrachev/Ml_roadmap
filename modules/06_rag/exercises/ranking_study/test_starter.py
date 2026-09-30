"""Student composition must call real prerequisite metrics, never test doubles."""

from pathlib import Path
from typing import Any

import pytest

from roadmap_tools.exercise import exercise_call

from . import evidence
from .starter import run_study

pytestmark = pytest.mark.student_exercise


def test_real_metric_composition_and_saved_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"evaluation": 0, "regression": 0}
    real_evaluation = evidence.evaluation.evaluate_retrieval
    real_regression = evidence.regression.compare_retrieval

    def evaluate(*args: Any, **kwargs: Any) -> Any:
        calls["evaluation"] += 1
        return real_evaluation(*args, **kwargs)

    def compare(*args: Any, **kwargs: Any) -> Any:
        calls["regression"] += 1
        return real_regression(*args, **kwargs)

    monkeypatch.setattr(evidence.evaluation, "evaluate_retrieval", evaluate)
    monkeypatch.setattr(evidence.regression, "compare_retrieval", compare)
    root = tmp_path / "study"
    result = exercise_call(run_study, root)
    assert result.resolve() == (root / "manifest.json").resolve()
    assert calls["evaluation"] >= 2
    assert calls["regression"] >= 1
    evidence.validate_evidence(root)


def test_preserves_existing_output(tmp_path: Path) -> None:
    marker = tmp_path / "notes.txt"
    marker.write_text("keep")
    with pytest.raises(FileExistsError):
        exercise_call(run_study, tmp_path)
    assert marker.read_text() == "keep"
