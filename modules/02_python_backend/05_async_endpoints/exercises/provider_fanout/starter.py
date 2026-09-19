"""Starter boundary for concurrent provider quote retrieval."""

from collections.abc import Awaitable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class QuoteRequest:
    currency: str
    amount: Decimal


@dataclass(frozen=True)
class Quote:
    provider: str
    amount: Decimal
    currency: str


class QuoteGateway(Protocol):
    async def fetch_quote(self, request: QuoteRequest) -> Quote: ...


def fetch_provider_quotes(
    gateways: Sequence[QuoteGateway], request: QuoteRequest
) -> Awaitable[list[Quote]]:
    """Fetch independent gateway quotes concurrently in input order."""

    raise NotImplementedError("Implement concurrent provider fan-out")
