"""Checks for expanding temporal windows and untouched future rows."""

from importlib import import_module

import pytest

example = import_module("modules.04_machine_learning.02_validation.example")


def test_windows_keep_a_gap_and_never_include_final_test_rows() -> None:
    windows, final_test = example.weather_windows()
    assert final_test == [16, 17, 18, 19]
    assert len(windows) == 3
    previous_train: set[int] = set()
    for train, valid in windows:
        assert max(train) + 2 == min(valid)
        assert len(valid) == 3
        assert previous_train <= set(train)
        assert not set(train + valid) & set(final_test)
        previous_train = set(train)


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
