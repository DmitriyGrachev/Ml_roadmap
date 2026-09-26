"""Checks that prediction reuses learned preprocessing state."""

from importlib import import_module

import pytest

example = import_module("modules.04_machine_learning.03_preprocessing.example")


def test_prediction_does_not_refit_training_scaler() -> None:
    state = example.training_state()
    assert state["training_mean"] == pytest.approx(22 / 6)
    assert state["mean_after_prediction"] == state["training_mean"]
    assert 0.5 < state["probability"] <= 1.0


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
