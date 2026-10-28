"""Teacher control flow results, independently calculated before implementation."""

from importlib import import_module
from typing import Any

import pytest


def demo() -> Any:
    return import_module("modules.01_python_core.00_environment.basics_demo")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("  oak ", "keep:OAK"), ("", "skip"), ("  ", "skip"), ("sequoia", "review:long")],
)
def test_label_branch_uses_trimmed_text(raw: str, expected: str) -> None:
    assert demo().label_action(raw) == expected


def test_for_loop_preserves_order_and_input() -> None:
    labels = [" oak ", "", "sequoia"]
    assert demo().trace_labels(labels) == [
        (" oak ", "keep:OAK"),
        ("", "skip"),
        ("sequoia", "review:long"),
    ]
    assert labels == [" oak ", "", "sequoia"]
    assert demo().trace_labels([]) == []


def test_while_countdown_stops_before_zero() -> None:
    assert demo().countdown(3) == [3, 2, 1]
    assert demo().countdown(0) == []


@pytest.mark.parametrize("start", [-1, True, 1.5])
def test_countdown_rejects_invalid_start(start: object) -> None:
    with pytest.raises(ValueError, match="start"):
        demo().countdown(start)


def test_range_and_return_are_observable(capsys: pytest.CaptureFixture[str]) -> None:
    demo().main()
    assert capsys.readouterr().out.splitlines() == [
        "2 + 3 * 4 = 14",
        "range(1, 4) = [1, 2, 3]",
        "' oak ' -> keep:OAK",
        "'' -> skip",
        "'sequoia' -> review:long",
        "countdown(3) = [3, 2, 1]",
        "return is a value: keep:PINE",
    ]
