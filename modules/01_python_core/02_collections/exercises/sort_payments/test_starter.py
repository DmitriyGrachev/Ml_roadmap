"""Tests for the sort-payments student exercise."""

from datetime import datetime
from decimal import Decimal

import pytest

from roadmap_tools import exercise_call

from .starter import PaymentRow, sort_payments


def payment(payment_id: str, amount: str, timestamp: str) -> PaymentRow:
    return {
        "id": payment_id,
        "amount": Decimal(amount),
        "timestamp": datetime.fromisoformat(timestamp),
    }


@pytest.mark.student_exercise
def test_sort_payments_uses_amount_timestamp_and_id_keys() -> None:
    payments = [
        payment("pay-c", "8.00", "2026-09-19T09:00:00+00:00"),
        payment("pay-b", "10.00", "2026-09-19T10:00:00+00:00"),
        payment("pay-a", "10.00", "2026-09-19T10:00:00+00:00"),
        payment("pay-d", "10.00", "2026-09-19T08:00:00+00:00"),
    ]

    assert [row["id"] for row in exercise_call(sort_payments, payments)] == [
        "pay-d",
        "pay-a",
        "pay-b",
        "pay-c",
    ]


@pytest.mark.student_exercise
def test_sort_payments_does_not_mutate_the_original_list() -> None:
    payments = [
        payment("pay-low", "1.00", "2026-09-19T09:00:00+00:00"),
        payment("pay-high", "2.00", "2026-09-19T09:00:00+00:00"),
    ]
    original = payments.copy()

    exercise_call(sort_payments, payments)

    assert payments == original


@pytest.mark.student_exercise
def test_sort_payments_accepts_a_one_shot_generator() -> None:
    payments = (
        row
        for row in (
            payment("pay-low", "1.00", "2026-09-19T09:00:00+00:00"),
            payment("pay-high", "2.00", "2026-09-19T09:00:00+00:00"),
        )
    )

    assert [row["id"] for row in exercise_call(sort_payments, payments)] == [
        "pay-high",
        "pay-low",
    ]


@pytest.mark.student_exercise
def test_sort_payments_returns_empty_list_for_empty_input() -> None:
    assert exercise_call(sort_payments, []) == []


def test_sort_payments_rejects_blank_payment_ids() -> None:
    with pytest.raises(ValueError, match="payment ID"):
        exercise_call(sort_payments, [payment(" ", "1.00", "2026-09-19T09:00:00+00:00")])


def test_sort_payments_rejects_non_decimal_amounts() -> None:
    row = {
        "id": "pay-001",
        "amount": "1.00",
        "timestamp": datetime.fromisoformat("2026-09-19T09:00:00+00:00"),
    }

    with pytest.raises(ValueError, match="payment amount"):
        exercise_call(sort_payments, [row])


def test_sort_payments_rejects_naive_timestamps() -> None:
    row: PaymentRow = {
        "id": "pay-001",
        "amount": Decimal("1.00"),
        "timestamp": datetime(2026, 9, 19, 9, tzinfo=None),
    }

    with pytest.raises(ValueError, match="timezone-aware"):
        exercise_call(sort_payments, [row])
