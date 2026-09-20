import asyncio
from collections.abc import Awaitable
from contextlib import suppress
from decimal import Decimal

import pytest

from roadmap_tools import exercise_call

from . import starter


def start_fetch(
    gateways: list[starter.QuoteGateway], request: starter.QuoteRequest
) -> Awaitable[list[starter.Quote]]:
    return exercise_call(starter.fetch_provider_quotes, gateways, request)


async def fetch_quotes(
    gateways: list[starter.QuoteGateway], request: starter.QuoteRequest
) -> list[starter.Quote]:
    return await start_fetch(gateways, request)


async def await_fetch(operation: Awaitable[list[starter.Quote]]) -> list[starter.Quote]:
    return await operation


class GatedGateway:
    def __init__(self, provider: str, amount: Decimal, release: asyncio.Event) -> None:
        self.provider = provider
        self.amount = amount
        self.release = release
        self.started = asyncio.Event()

    async def fetch_quote(self, request: starter.QuoteRequest) -> starter.Quote:
        self.started.set()
        await self.release.wait()
        return starter.Quote(provider=self.provider, amount=self.amount, currency=request.currency)


class RaisingGateway:
    async def fetch_quote(self, request: starter.QuoteRequest) -> starter.Quote:
        raise ValueError(f"{request.currency} is unavailable")


class CancelledGateway:
    async def fetch_quote(self, request: starter.QuoteRequest) -> starter.Quote:
        raise asyncio.CancelledError


@pytest.mark.asyncio
async def test_quotes_start_concurrently_and_return_in_gateway_order() -> None:
    release = asyncio.Event()
    first = GatedGateway("first", Decimal("1.25"), release)
    second = GatedGateway("second", Decimal("1.50"), release)
    request = starter.QuoteRequest(currency="USD", amount=Decimal("10.00"))
    task: asyncio.Task[list[starter.Quote]] = asyncio.create_task(
        await_fetch(start_fetch([first, second], request))
    )

    try:
        await first.started.wait()
        assert second.started.is_set()
        release.set()
        assert await task == [
            starter.Quote(provider="first", amount=Decimal("1.25"), currency="USD"),
            starter.Quote(provider="second", amount=Decimal("1.50"), currency="USD"),
        ]
    finally:
        release.set()
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


@pytest.mark.asyncio
async def test_empty_gateway_list_returns_no_quotes() -> None:
    request = starter.QuoteRequest(currency="EUR", amount=Decimal("2.00"))

    assert await fetch_quotes([], request) == []


@pytest.mark.asyncio
async def test_gateway_exception_propagates() -> None:
    request = starter.QuoteRequest(currency="GBP", amount=Decimal("3.00"))

    with pytest.raises(ValueError, match="GBP is unavailable"):
        await fetch_quotes([RaisingGateway()], request)


@pytest.mark.asyncio
async def test_gateway_cancellation_propagates() -> None:
    request = starter.QuoteRequest(currency="GBP", amount=Decimal("3.00"))

    with pytest.raises(asyncio.CancelledError):
        await fetch_quotes([CancelledGateway()], request)
