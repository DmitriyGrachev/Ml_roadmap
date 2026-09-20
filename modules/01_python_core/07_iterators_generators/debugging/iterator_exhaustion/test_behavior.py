"""Behavior test for the iterator-exhaustion debugging fixture."""

from decimal import Decimal

import pytest

from .broken import summarize_amounts


@pytest.mark.xfail(reason="intentional broken starter", strict=False)
def test_one_shot_amounts_are_counted_and_totaled() -> None:
    amounts = (Decimal(value) for value in ("10.25", "-0.25", "4.00"))

    assert summarize_amounts(amounts) == (3, Decimal("14.00"))
