"""Event gates make concurrency checks deterministic and independent of network access."""

import asyncio
from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import fetch_bounded

pytestmark = pytest.mark.student_exercise


@pytest.mark.parametrize("limit", [1, 2, 5])
def test_bounds_active_work_and_preserves_input_order(limit: int) -> None:
    async def scenario() -> None:
        active = 0
        peak = 0
        entered: asyncio.Queue[str] = asyncio.Queue()
        gates = {key: asyncio.Event() for key in ["a", "b", "c"]}

        async def fetch(key: str) -> str:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            entered.put_nowait(key)
            try:
                await gates[key].wait()
                return key.upper()
            finally:
                active -= 1

        task = asyncio.create_task(fetch_bounded(["a", "b", "c"], fetch, limit))

        async def next_entry() -> str:
            waiting = asyncio.create_task(entered.get())
            try:
                done, _ = await asyncio.wait(
                    {task, waiting}, timeout=1, return_when=asyncio.FIRST_COMPLETED
                )
                if task in done:
                    task.result()
                assert waiting in done, "fetches did not reach the expected concurrency"
                return waiting.result()
            finally:
                waiting.cancel()
                await asyncio.gather(waiting, return_exceptions=True)

        try:
            first_wave = [await next_entry() for _ in range(min(limit, 3))]
            assert peak == min(limit, 3)
            assert entered.empty()
            for key in reversed(first_wave):
                gates[key].set()
            for _ in range(3 - len(first_wave)):
                gates[await next_entry()].set()
            assert await asyncio.wait_for(task, 1) == ["A", "B", "C"]
            assert peak <= limit
            assert active == 0
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    exercise_call(asyncio.run, scenario())


def test_duplicates_are_separate_requests_and_input_is_unchanged() -> None:
    async def scenario() -> None:
        calls: list[str] = []

        async def fetch(key: str) -> str:
            calls.append(key)
            return f"reading:{key}"

        keys = ["north", "north", "south"]
        assert await fetch_bounded(keys, fetch, 2) == [
            "reading:north",
            "reading:north",
            "reading:south",
        ]
        assert sorted(calls) == ["north", "north", "south"]
        assert keys == ["north", "north", "south"]

    exercise_call(asyncio.run, scenario())


def test_empty_input_never_calls_fetch() -> None:
    async def scenario() -> None:
        async def fetch(key: str) -> str:
            raise AssertionError(f"unexpected request: {key}")

        assert await fetch_bounded([], fetch, 2) == []

    exercise_call(asyncio.run, scenario())


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
@pytest.mark.parametrize("keys", [[], ["north"]])
def test_invalid_limit_is_rejected_before_dispatch(limit: object, keys: list[str]) -> None:
    async def scenario() -> None:
        async def fetch(key: str) -> str:
            raise AssertionError(f"unexpected request: {key}")

        with pytest.raises(ValueError, match="limit"):
            await fetch_bounded(keys, fetch, cast(int, limit))

    exercise_call(asyncio.run, scenario())


def test_failure_cancels_and_awaits_other_active_fetches() -> None:
    async def scenario() -> None:
        started = asyncio.Event()
        cleaned = asyncio.Event()
        original_error = LookupError("station missing")

        async def fetch(key: str) -> str:
            if key == "bad":
                await started.wait()
                raise original_error
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleaned.set()
            return "unreachable"

        with pytest.raises(LookupError, match="station missing") as caught:
            await asyncio.wait_for(fetch_bounded(["bad", "slow"], fetch, 2), 1)
        assert caught.value is original_error
        assert cleaned.is_set()

    exercise_call(asyncio.run, scenario())
