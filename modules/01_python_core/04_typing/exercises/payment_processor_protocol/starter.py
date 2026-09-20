"""Student boundary for structural payment-processor delegation."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Payment:
    """A payment submitted for authorization."""

    id: str
    amount: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class Authorization:
    """The immutable result returned by a payment processor."""

    payment_id: str
    approved: bool
    reference: str | None


class PaymentProcessor(Protocol):
    """Structural boundary implemented by compatible payment processors."""

    def authorize(self, payment: Payment) -> Authorization:
        """Authorize one payment and return the provider result."""
        ...


def authorize_payment(
    processor: PaymentProcessor,
    payment: Payment,
) -> Authorization:
    """Delegate authorization once and preserve processor outcomes."""
    raise NotImplementedError("delegate payment authorization")
