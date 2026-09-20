"""Acceptance tests for controlled asynchronous quote fan-out."""

import asyncio
from contextlib import suppress
from decimal import Decimal

import pytest

from roadmap_tools import exercise_call

from .starter import fetch_quotes


class QuoteProviderError(Exception):
    """A domain error raised by the controlled provider double."""


@pytest.mark.student_exercise
def test_fetch_quotes_starts_every_call_before_controlled_release() -> None:
    async def scenario() -> list[Decimal]:
        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        started: set[str] = set()
        all_started = asyncio.Event()
        release = asyncio.Event()

        async def fetch(symbol: str) -> Decimal:
            started.add(symbol)
            if len(started) == len(symbols):
                all_started.set()
            await release.wait()
            return Decimal("1")

        report_task = asyncio.create_task(fetch_quotes(symbols, fetch))
        started_task = asyncio.create_task(all_started.wait())
        try:
            done, _pending = await asyncio.wait(
                {report_task, started_task},
                timeout=1.0,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if report_task in done:
                early_result = await report_task
                pytest.fail(f"fetch_quotes returned before all calls started: {early_result!r}")
            if started_task not in done:
                pytest.fail("fetch_quotes did not start all calls concurrently")

            assert started == set(symbols)
            assert report_task.done() is False
            release.set()
            return await asyncio.wait_for(report_task, timeout=1.0)
        finally:
            started_task.cancel()
            if not report_task.done():
                report_task.cancel()
            with suppress(asyncio.CancelledError):
                await started_task
            with suppress(asyncio.CancelledError):
                await report_task

    assert exercise_call(asyncio.run, scenario()) == [Decimal("1")] * 3


@pytest.mark.student_exercise
def test_fetch_quotes_preserves_input_order_when_calls_finish_out_of_order() -> None:
    async def scenario() -> tuple[list[Decimal], list[str]]:
        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        values = {
            "EURUSD": Decimal("1.10"),
            "GBPUSD": Decimal("1.30"),
            "USDJPY": Decimal("145.20"),
        }
        started: set[str] = set()
        all_started = asyncio.Event()
        releases = {symbol: asyncio.Event() for symbol in symbols}
        completions = {symbol: asyncio.Event() for symbol in symbols}
        completed: list[str] = []

        async def fetch(symbol: str) -> Decimal:
            started.add(symbol)
            if len(started) == len(symbols):
                all_started.set()
            await releases[symbol].wait()
            completed.append(symbol)
            completions[symbol].set()
            return values[symbol]

        report_task = asyncio.create_task(fetch_quotes(symbols, fetch))
        try:
            await asyncio.wait_for(all_started.wait(), timeout=1.0)
            for symbol in ("USDJPY", "EURUSD", "GBPUSD"):
                releases[symbol].set()
                await asyncio.wait_for(completions[symbol].wait(), timeout=1.0)
            return await asyncio.wait_for(report_task, timeout=1.0), completed
        finally:
            if not report_task.done():
                report_task.cancel()
            with suppress(asyncio.CancelledError):
                await report_task

    result, completion_order = exercise_call(asyncio.run, scenario())

    assert completion_order == ["USDJPY", "EURUSD", "GBPUSD"]
    assert result == [Decimal("1.10"), Decimal("1.30"), Decimal("145.20")]


@pytest.mark.student_exercise
def test_fetch_quotes_returns_empty_without_calling_fetcher() -> None:
    async def fetch(_symbol: str) -> Decimal:
        raise AssertionError("fetcher must not be called for empty input")

    assert exercise_call(asyncio.run, fetch_quotes([], fetch)) == []


@pytest.mark.student_exercise
def test_fetch_quotes_propagates_the_child_exception() -> None:
    error = QuoteProviderError("provider unavailable")

    async def fetch(symbol: str) -> Decimal:
        if symbol == "BAD":
            raise error
        await asyncio.sleep(0)
        return Decimal("1.00")

    async def scenario() -> None:
        with pytest.raises(QuoteProviderError) as caught:
            await fetch_quotes(["EURUSD", "BAD"], fetch)
        assert caught.value is error

    exercise_call(asyncio.run, scenario())
