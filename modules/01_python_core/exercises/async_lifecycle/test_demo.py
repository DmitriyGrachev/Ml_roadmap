"""Catch leaked siblings, lost order, swallowed cancellation and unbounded work."""

import asyncio

import pytest

from .demo import run_batch


def test_bounded_batch_preserves_order_and_closes_happy_path() -> None:
    async def scenario() -> None:
        entered: asyncio.Queue[str] = asyncio.Queue()
        gates = {key: asyncio.Event() for key in ["a", "b", "c"]}
        active: set[str] = set()
        peak = 0

        async def fetch(key: str) -> str:
            nonlocal peak
            active.add(key)
            peak = max(peak, len(active))
            entered.put_nowait(key)
            try:
                await gates[key].wait()
                return key.upper()
            finally:
                active.remove(key)

        parent = asyncio.create_task(run_batch(["a", "b", "c"], fetch, 2))
        try:
            first = await asyncio.wait_for(entered.get(), 2)
            second = await asyncio.wait_for(entered.get(), 2)
            assert peak == 2
            assert entered.empty()
            gates[second].set()
            third = await asyncio.wait_for(entered.get(), 2)
            gates[third].set()
            gates[first].set()
            assert await asyncio.wait_for(parent, 2) == ["A", "B", "C"]
            assert active == set()
            assert peak == 2
        finally:
            parent.cancel()
            await asyncio.gather(parent, return_exceptions=True)

    asyncio.run(scenario())


def test_sibling_failure_waits_for_cleanup_and_leaves_no_owned_tasks() -> None:
    async def scenario() -> None:
        started = asyncio.Event()
        cleaned = asyncio.Event()
        owned: set[asyncio.Task[object]] = set()

        async def fetch(key: str) -> str:
            task = asyncio.current_task()
            assert task is not None
            owned.add(task)
            if key == "broken":
                await started.wait()
                raise LookupError("missing source")
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleaned.set()
            return "unreachable"

        with pytest.raises(ExceptionGroup) as caught:
            await asyncio.wait_for(run_batch(["broken", "slow", "queued"], fetch, 2), 2)
        assert any(isinstance(error, LookupError) for error in caught.value.exceptions)
        assert cleaned.is_set()
        assert all(task.done() for task in owned)

    asyncio.run(scenario())


def test_external_cancellation_is_propagated_after_cleanup() -> None:
    async def scenario() -> None:
        started = asyncio.Event()
        cleaned = asyncio.Event()
        owned: list[asyncio.Task[object]] = []

        async def fetch(key: str) -> str:
            task = asyncio.current_task()
            assert task is not None
            owned.append(task)
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleaned.set()
            return key

        parent = asyncio.create_task(run_batch(["active", "queued"], fetch, 1))
        try:
            await asyncio.wait_for(started.wait(), 2)
            parent.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(parent, 2)
            assert cleaned.is_set()
            assert all(task.done() for task in owned)
        finally:
            parent.cancel()
            await asyncio.gather(parent, return_exceptions=True)

    asyncio.run(scenario())


def test_timeout_cancels_work_and_waits_for_cleanup() -> None:
    async def scenario() -> None:
        cleaned = asyncio.Event()

        async def fetch(key: str) -> str:
            try:
                await asyncio.Event().wait()
            finally:
                cleaned.set()
            return key

        with pytest.raises(TimeoutError):
            await run_batch(["blocked"], fetch, 1, timeout=0.01)
        assert cleaned.is_set()

    asyncio.run(scenario())


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_limit_rejected_without_starting_work(limit: int) -> None:
    async def fetch(key: str) -> str:
        raise AssertionError("invalid batch started work")

    with pytest.raises(ValueError, match="limit"):
        asyncio.run(run_batch([], fetch, limit))


def test_empty_batch_is_empty() -> None:
    async def fetch(key: str) -> str:
        raise AssertionError("empty batch started work")

    assert asyncio.run(run_batch([], fetch, 1)) == []
