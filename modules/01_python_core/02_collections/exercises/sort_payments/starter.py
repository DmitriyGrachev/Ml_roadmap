"""Student boundary for sorting typed payment rows."""

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from typing import TypedDict


class PaymentRow(TypedDict):
    """A payment accepted by the sorting boundary."""

    id: str
    amount: Decimal
    timestamp: datetime


def sort_payments(payments: Iterable[PaymentRow]) -> list[PaymentRow]:
    """Sort payments by amount, timestamp, and identifier without mutation."""
    payment_rows = list(payments)
    for payment in payment_rows:
        payment_id = payment.get("id")
        if not isinstance(payment_id, str) or not payment_id.strip():
            raise ValueError("payment ID must be a nonblank string")
        if not isinstance(payment.get("amount"), Decimal):
            raise ValueError("payment amount must be a Decimal")
        timestamp = payment.get("timestamp")
        if not isinstance(timestamp, datetime) or timestamp.utcoffset() is None:
            raise ValueError("payment timestamp must be timezone-aware")

    raise NotImplementedError("sort payments")
