"""Tests for the configurable transaction-filter exercise."""

from decimal import Decimal
from typing import Any, cast

import pytest

from roadmap_tools import exercise_call

from .starter import TransactionRow, make_transaction_filter


def transaction(
    *,
    transaction_id: str = "txn-001",
    user_id: str = "user-001",
    amount: str = "25.00",
    currency: str = "USD",
    status: str = "posted",
) -> TransactionRow:
    return {
        "id": transaction_id,
        "user_id": user_id,
        "amount": Decimal(amount),
        "currency": currency,
        "status": status,
    }


def test_make_transaction_filter_is_keyword_only() -> None:
    positional_call = cast(Any, make_transaction_filter)

    with pytest.raises(TypeError):
        exercise_call(positional_call, Decimal("10.00"))


def test_make_transaction_filter_rejects_a_negative_minimum() -> None:
    with pytest.raises(ValueError, match="minimum"):
        exercise_call(make_transaction_filter, minimum=Decimal("-0.01"))


@pytest.mark.student_exercise
def test_none_currencies_leave_currency_unrestricted() -> None:
    transaction_filter = exercise_call(make_transaction_filter, currencies=None)

    assert exercise_call(transaction_filter, transaction(currency="JPY")) is True


@pytest.mark.student_exercise
def test_filter_uses_an_inclusive_minimum_amount() -> None:
    transaction_filter = exercise_call(
        make_transaction_filter,
        minimum=Decimal("25.00"),
    )

    assert exercise_call(transaction_filter, transaction(amount="25.00")) is True
    assert exercise_call(transaction_filter, transaction(amount="24.99")) is False


@pytest.mark.student_exercise
def test_filter_restricts_rows_to_configured_currencies() -> None:
    transaction_filter = exercise_call(
        make_transaction_filter,
        currencies=frozenset({"USD", "EUR"}),
    )

    assert exercise_call(transaction_filter, transaction(currency="EUR")) is True
    assert exercise_call(transaction_filter, transaction(currency="GBP")) is False


@pytest.mark.student_exercise
def test_filter_composes_the_optional_predicate() -> None:
    def is_posted(row: TransactionRow) -> bool:
        return row["status"] == "posted"

    transaction_filter = exercise_call(
        make_transaction_filter,
        minimum=Decimal("10.00"),
        currencies=frozenset({"USD"}),
        predicate=is_posted,
    )

    assert exercise_call(transaction_filter, transaction(status="posted")) is True
    assert exercise_call(transaction_filter, transaction(status="reversed")) is False


@pytest.mark.student_exercise
def test_true_custom_predicate_does_not_override_the_minimum() -> None:
    def always_true(_row: TransactionRow) -> bool:
        return True

    transaction_filter = exercise_call(
        make_transaction_filter,
        minimum=Decimal("25.00"),
        predicate=always_true,
    )

    assert exercise_call(transaction_filter, transaction(amount="24.99")) is False


@pytest.mark.student_exercise
def test_true_custom_predicate_does_not_override_allowed_currencies() -> None:
    def always_true(_row: TransactionRow) -> bool:
        return True

    transaction_filter = exercise_call(
        make_transaction_filter,
        currencies=frozenset({"USD"}),
        predicate=always_true,
    )

    assert exercise_call(transaction_filter, transaction(currency="EUR")) is False


@pytest.mark.student_exercise
def test_filter_captures_an_immutable_currency_configuration() -> None:
    mutable_currencies = {"USD"}
    configured_currencies = cast(frozenset[str], mutable_currencies)
    transaction_filter = exercise_call(
        make_transaction_filter,
        currencies=configured_currencies,
    )

    mutable_currencies.clear()

    assert exercise_call(transaction_filter, transaction(currency="USD")) is True
    assert exercise_call(transaction_filter, transaction(currency="EUR")) is False
