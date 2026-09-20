"""Student boundary for isolating one provider interaction in a test."""

from decimal import Decimal
from typing import Protocol


class QuoteProvider(Protocol):
    """Structural boundary for an external quote provider."""

    def quote(self, merchant_id: str, currency: str) -> Decimal:
        """Return the exact quote for a merchant and target currency."""
        ...


def request_quote(
    provider: QuoteProvider,
    merchant_id: str,
    currency: str,
) -> Decimal:
    """Request exactly one quote using the original arguments."""
    raise NotImplementedError("request one provider quote")
