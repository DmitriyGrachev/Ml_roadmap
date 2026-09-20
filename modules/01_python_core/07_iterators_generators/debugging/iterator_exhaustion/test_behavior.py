"""Behavior test for the iterator-exhaustion debugging fixture."""

from decimal import Decimal

import pytest

from .broken import summarize_amounts


@pytest.mark.xfail(reason="intentional broken starter", strict=False)
def test_one_shot_amounts_are_counted_and_totaled() -> None:
    amounts = (
        Decimal(value)
        for value in (
            "0.1000000000000000001",
            "0.2000000000000000002",
            "13.0000000000000000003",
        )
    )

    count, total = summarize_amounts(amounts)

    assert count == 3
    assert total == Decimal("13.3000000000000000006")
    assert isinstance(total, Decimal)


def test_empty_amounts_have_a_decimal_zero_total() -> None:
    count, total = summarize_amounts([])

    assert count == 0
    assert total == Decimal("0")
    assert isinstance(total, Decimal)


def test_reiterable_amounts_keep_exact_decimal_arithmetic() -> None:
    amounts = (
        Decimal("0.1000000000000000001"),
        Decimal("0.2000000000000000002"),
    )

    count, total = summarize_amounts(amounts)

    assert count == 2
    assert total == Decimal("0.3000000000000000003")
    assert isinstance(total, Decimal)
