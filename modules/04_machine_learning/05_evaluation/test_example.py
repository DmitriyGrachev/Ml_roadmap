"""Checks for a route error slice hidden by an overall average."""

from importlib import import_module

import pytest

example = import_module("modules.04_machine_learning.05_evaluation.example")


def test_error_slices_and_squared_penalty_have_distinct_meanings() -> None:
    result = example.route_errors()
    assert result["overall_mae_minutes"] == 3.5
    assert result["overall_rmse_minutes"] == pytest.approx(26.5**0.5)
    assert result["flat_mae_minutes"] == 1.0
    assert result["hill_mae_minutes"] == 6.0


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
