"""Acceptance tests for the frozen payment model."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from roadmap_tools import exercise_call

from .starter import Payment


def test_payment_is_frozen() -> None:
    payment = object.__new__(Payment)
    object.__setattr__(payment, "identifier", "pay-001")
    object.__setattr__(payment, "amount", Decimal("1.00"))
    object.__setattr__(payment, "currency", "EUR")

    with pytest.raises(FrozenInstanceError):
        exercise_call(setattr, payment, "amount", Decimal("2.00"))


@pytest.mark.student_exercise
def test_payment_accepts_a_valid_value_object() -> None:
    payment = exercise_call(Payment, "pay-001", Decimal("19.95"), "EUR")

    assert payment.identifier == "pay-001"
    assert payment.amount == Decimal("19.95")
    assert payment.currency == "EUR"


@pytest.mark.student_exercise
@pytest.mark.parametrize("identifier", ["", "   ", 42])
def test_payment_rejects_a_blank_or_non_string_identifier(identifier: object) -> None:
    with pytest.raises(ValueError, match="identifier"):
        exercise_call(Payment, identifier, Decimal("1.00"), "EUR")


@pytest.mark.student_exercise
@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0"),
        Decimal("-0.01"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_payment_rejects_a_non_positive_or_non_finite_amount(amount: Decimal) -> None:
    with pytest.raises(ValueError, match="amount"):
        exercise_call(Payment, "pay-001", amount, "EUR")


@pytest.mark.student_exercise
@pytest.mark.parametrize("amount", [1, 1.0, "1.00"])
def test_payment_rejects_a_non_decimal_amount(amount: object) -> None:
    with pytest.raises(ValueError, match="amount"):
        exercise_call(Payment, "pay-001", amount, "EUR")


@pytest.mark.student_exercise
@pytest.mark.parametrize("currency", ["eur", "EU", "EURO", "E1R", " EUR", "ÉUR", 978])
def test_payment_rejects_an_invalid_currency(currency: object) -> None:
    with pytest.raises(ValueError, match="currency"):
        exercise_call(Payment, "pay-001", Decimal("1.00"), currency)
