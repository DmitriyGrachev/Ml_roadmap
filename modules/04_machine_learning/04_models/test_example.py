"""Checks that the small parameter search produces repeatable valid scores."""

from importlib import import_module

import pytest

example = import_module("modules.04_machine_learning.04_models.example")


def test_search_is_reproducible_and_selects_a_declared_candidate() -> None:
    result = example.select_tree()
    assert result == example.select_tree()
    assert result["selected_depth"] in {1, 2, 3}
    assert 0.0 <= result["validation_balanced_accuracy"] <= 1.0
    assert 0.0 <= result["test_balanced_accuracy"] <= 1.0


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
