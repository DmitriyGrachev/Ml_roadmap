"""Tests for the structural payment-processor protocol exercise."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from roadmap_tools import exercise_call

from .starter import (
    Authorization,
    Payment,
    PaymentProcessor,
    authorize_payment,
)


class RecordingProcessor:
    """Structural protocol implementation with no explicit inheritance."""

    def __init__(self, authorization: Authorization) -> None:
        self.authorization = authorization
        self.calls: list[Payment] = []

    def authorize(self, payment: Payment) -> Authorization:
        self.calls.append(payment)
        return self.authorization


class PaymentDeclinedError(Exception):
    """Example domain error owned by a payment provider."""


class DecliningProcessor:
    def __init__(self, error: PaymentDeclinedError) -> None:
        self.error = error
        self.calls: list[Payment] = []

    def authorize(self, payment: Payment) -> Authorization:
        self.calls.append(payment)
        raise self.error


def payment() -> Payment:
    return exercise_call(
        Payment,
        id="pay-001",
        amount=Decimal("19.95"),
        currency="USD",
    )


def authorization() -> Authorization:
    return exercise_call(
        Authorization,
        payment_id="pay-001",
        approved=True,
        reference="auth-001",
    )


@pytest.mark.student_exercise
def test_authorize_payment_accepts_a_structural_processor_and_delegates_once() -> None:
    expected = authorization()
    processor = RecordingProcessor(expected)
    structural_processor: PaymentProcessor = processor
    candidate_payment = payment()

    result = exercise_call(authorize_payment, structural_processor, candidate_payment)

    assert result is expected
    assert processor.calls == [candidate_payment]


@pytest.mark.student_exercise
def test_authorize_payment_propagates_the_same_domain_exception() -> None:
    error = PaymentDeclinedError("insufficient funds")
    processor = DecliningProcessor(error)
    structural_processor: PaymentProcessor = processor
    candidate_payment = payment()

    with pytest.raises(PaymentDeclinedError) as raised:
        exercise_call(authorize_payment, structural_processor, candidate_payment)

    assert raised.value is error
    assert processor.calls == [candidate_payment]


@pytest.mark.parametrize(
    ("record", "field", "replacement"),
    [
        (payment(), "currency", "EUR"),
        (authorization(), "approved", False),
    ],
)
def test_payment_records_are_frozen(
    record: Payment | Authorization,
    field: str,
    replacement: object,
) -> None:
    with pytest.raises(FrozenInstanceError):
        exercise_call(setattr, record, field, replacement)
