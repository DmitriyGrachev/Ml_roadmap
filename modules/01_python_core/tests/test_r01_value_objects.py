"""Author checks: invalid spans and non-finite probes must not escape validation."""

import runpy
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def lesson() -> dict[str, Any]:
    return runpy.run_path(str(Path(__file__).parents[1] / "05_data_modeling/walkthrough.py"))


def test_span_uses_half_open_boundaries_and_value_equality(lesson: dict[str, Any]) -> None:
    span = lesson["PageSpan"](2, 5)
    assert span.length == 3
    assert span == lesson["PageSpan"](2, 5)
    assert lesson["PageSpan"](5, 5).length == 0
    with pytest.raises(FrozenInstanceError):
        span.stop = 9


@pytest.mark.parametrize(("start", "stop"), [(-1, 2), (3, 2), ("0", 2), (0, 2.5), (True, 3)])
def test_span_rejects_invalid_endpoints(
    lesson: dict[str, Any], start: object, stop: object
) -> None:
    with pytest.raises(ValueError, match="endpoints"):
        lesson["PageSpan"](start, stop)


@pytest.mark.parametrize(("value", "want"), [("-2.5", -1), ("0", 0), ("2.5", 1)])
def test_decimal_probe_classifies_finite_values(
    lesson: dict[str, Any], value: str, want: int
) -> None:
    assert lesson["finite_sign"](Decimal(value)) == want


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), 1])
def test_decimal_probe_rejects_before_ordering(lesson: dict[str, Any], value: object) -> None:
    with pytest.raises(ValueError, match="finite Decimal"):
        lesson["finite_sign"](value)


@pytest.mark.parametrize(
    ("text", "want"), [("42", True), ("٤٢", False), ("", False), ("4a", False)]
)
def test_digit_probe_obeys_ascii_contract(lesson: dict[str, Any], text: str, want: bool) -> None:
    assert lesson["is_ascii_digits"](text) is want
