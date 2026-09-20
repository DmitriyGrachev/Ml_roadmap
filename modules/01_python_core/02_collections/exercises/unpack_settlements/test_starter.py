"""Tests for the unpack-settlements student exercise."""

from decimal import Decimal
from typing import cast

import pytest

from roadmap_tools import exercise_call

from .starter import parse_settlement


@pytest.mark.student_exercise
def test_parse_settlement_returns_a_decimal_without_float_conversion() -> None:
    assert exercise_call(parse_settlement, ["txn-001", "0.10", "EUR"]) == (
        "txn-001",
        Decimal("0.10"),
        "EUR",
    )


@pytest.mark.parametrize("row", [[], ["txn-001"], ["txn-001", "1.00"], ["a", "1", "EUR", "x"]])
def test_parse_settlement_rejects_wrong_field_counts(row: list[str]) -> None:
    with pytest.raises(ValueError, match="exactly three fields"):
        exercise_call(parse_settlement, row)


def test_parse_settlement_rejects_invalid_decimal_text() -> None:
    with pytest.raises(ValueError, match="valid decimal"):
        exercise_call(parse_settlement, ["txn-001", "not-an-amount", "EUR"])


@pytest.mark.parametrize(
    "amount",
    [0.1, 1, True, Decimal("1.00")],
    ids=["float", "int", "bool", "decimal"],
)
def test_parse_settlement_rejects_non_string_amounts(amount: object) -> None:
    row = cast(list[str], ["txn-001", amount, "EUR"])

    with pytest.raises(ValueError, match="decimal text"):
        exercise_call(parse_settlement, row)


@pytest.mark.parametrize("currency", ["", "   ", 42])
def test_parse_settlement_rejects_invalid_currency(currency: object) -> None:
    row = cast(list[str], ["txn-001", "1.00", currency])

    with pytest.raises(ValueError, match="currency"):
        exercise_call(parse_settlement, row)


@pytest.mark.parametrize("transaction_id", ["", "   ", 42])
def test_parse_settlement_rejects_invalid_transaction_id(transaction_id: object) -> None:
    row = cast(list[str], [transaction_id, "1.00", "EUR"])

    with pytest.raises(ValueError, match="transaction ID"):
        exercise_call(parse_settlement, row)
