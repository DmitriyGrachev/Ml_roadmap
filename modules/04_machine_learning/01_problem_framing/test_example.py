"""Checks for distinct baseline failure modes."""

from importlib import import_module

import pytest

example = import_module("modules.04_machine_learning.01_problem_framing.example")


def test_training_only_baselines_expose_positive_class_failure() -> None:
    assert example.baseline_scores() == pytest.approx(
        {"visits_mae": 2.0, "watering_accuracy": 0.75, "watering_recall": 0.0}
    )


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
