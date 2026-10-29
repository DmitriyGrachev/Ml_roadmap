"""Independent transfer: first success differs from the author's all-or-fail batch."""

import asyncio
from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import first_healthy

pytestmark = pytest.mark.student_exercise


async def next_or_failure(queue: asyncio.Queue[str], parent: asyncio.Task[str]) -> str:
    """Propagate an unfinished starter immediately instead of waiting for the watchdog."""
    waiting = asyncio.create_task(queue.get())
    try:
        done, _ = await asyncio.wait(
            {waiting, parent}, timeout=2, return_when=asyncio.FIRST_COMPLETED
        )
        if parent in done:
            parent.result()
        assert waiting in done, "replicas never reached the expected concurrency"
        return waiting.result()
    finally:
        waiting.cancel()
        await asyncio.gather(waiting, return_exceptions=True)


def test_first_success_bounds_work_and_awaits_losers() -> None:
    async def scenario() -> None:
        entered: asyncio.Queue[str] = asyncio.Queue()
        release = asyncio.Event()
        closed: set[str] = set()
        active = 0
        peak = 0
        before = asyncio.all_tasks()

        async def probe(key: str) -> str:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            entered.put_nowait(key)
            try:
                if key == "winner":
                    await release.wait()
                    return "healthy payload"
                await asyncio.Event().wait()
                return "unreachable"
            finally:
                active -= 1
                closed.add(key)

        parent = asyncio.create_task(first_healthy(["loser", "winner", "queued"], probe, 2))
        try:
            assert {
                await next_or_failure(entered, parent),
                await next_or_failure(entered, parent),
            } == {"loser", "winner"}
            assert entered.empty()
            release.set()
            assert await asyncio.wait_for(parent, 2) == "healthy payload"
            assert closed >= {"loser", "winner"}
            assert active == 0
            assert peak == 2
            assert asyncio.all_tasks() - before == set()
        finally:
            parent.cancel()
            await asyncio.gather(parent, return_exceptions=True)

    exercise_call(asyncio.run, scenario())


def test_failed_replica_does_not_cancel_later_success() -> None:
    async def scenario() -> None:
        calls: list[str] = []

        async def probe(key: str) -> str:
            calls.append(key)
            if key == "offline":
                raise OSError("replica unavailable")
            return "fresh prediction"

        assert await first_healthy(["offline", "online"], probe, 1) == "fresh prediction"
        assert calls == ["offline", "online"]

    exercise_call(asyncio.run, scenario())


@pytest.mark.parametrize("replicas", [[], ["a", "b"]])
def test_no_success_raises_lookup_error(replicas: list[str]) -> None:
    async def scenario() -> None:
        async def probe(key: str) -> str:
            raise OSError(key)

        with pytest.raises(LookupError):
            await first_healthy(replicas, probe, 2)

    exercise_call(asyncio.run, scenario())


def test_external_cancel_cleans_active_replica_and_propagates() -> None:
    async def scenario() -> None:
        entered: asyncio.Queue[str] = asyncio.Queue()
        cleaned = asyncio.Event()
        before = asyncio.all_tasks()

        async def probe(key: str) -> str:
            entered.put_nowait(key)
            try:
                await asyncio.Event().wait()
            finally:
                cleaned.set()
            return key

        parent = asyncio.create_task(first_healthy(["a", "b"], probe, 1))
        try:
            await next_or_failure(entered, parent)
            parent.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(parent, 2)
            assert cleaned.is_set()
            assert asyncio.all_tasks() - before == set()
        finally:
            parent.cancel()
            await asyncio.gather(parent, return_exceptions=True)

    exercise_call(asyncio.run, scenario())


def test_deadline_cleans_work_before_timeout_reaches_caller() -> None:
    async def scenario() -> None:
        cleaned = asyncio.Event()
        before = asyncio.all_tasks()

        async def probe(key: str) -> str:
            try:
                await asyncio.Event().wait()
            finally:
                cleaned.set()
            return key

        with pytest.raises(TimeoutError):
            await first_healthy(["a", "b"], probe, 1, timeout=0.01)
        assert cleaned.is_set()
        assert asyncio.all_tasks() - before == set()

    exercise_call(asyncio.run, scenario())


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_limit_is_rejected_even_for_empty_input(limit: object) -> None:
    async def scenario() -> None:
        async def probe(key: str) -> str:
            raise AssertionError("validation must precede dispatch")

        with pytest.raises(ValueError, match="limit"):
            await first_healthy([], probe, cast(int, limit))

    exercise_call(asyncio.run, scenario())


def test_duplicate_occurrences_are_distinct_attempts_without_input_mutation() -> None:
    async def scenario() -> None:
        calls = 0
        replicas = ["same", "same"]

        async def probe(key: str) -> str:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("first attempt unavailable")
            return key + ":recovered"

        assert await first_healthy(replicas, probe, 1) == "same:recovered"
        assert calls == 2
        assert replicas == ["same", "same"]

    exercise_call(asyncio.run, scenario())
