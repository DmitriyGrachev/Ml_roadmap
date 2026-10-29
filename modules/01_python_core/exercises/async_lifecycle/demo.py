"""Author example: bounded batch with structured cancellation."""

import asyncio
from collections.abc import Awaitable, Callable, Sequence


async def run_batch(
    keys: Sequence[str],
    fetch: Callable[[str], Awaitable[str]],
    limit: int,
    timeout: float | None = None,
) -> list[str]:
    """Return ordered results only after every owned task has terminated."""
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive integer")
    semaphore = asyncio.Semaphore(limit)

    async def bounded(key: str) -> str:
        async with semaphore:
            return await fetch(key)

    # timeout owns the whole batch, including time spent waiting for a permit.
    async with asyncio.timeout(timeout):
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(bounded(key)) for key in keys]
    return [task.result() for task in tasks]


async def main() -> None:
    async def fetch(key: str) -> str:
        try:
            # A cooperative I/O placeholder; the lesson tests use explicit events.
            await asyncio.sleep(0)
            return key.upper()
        finally:
            print(f"closed: {key}")

    print(await run_batch(["north", "south", "east"], fetch, limit=2, timeout=1))


if __name__ == "__main__":
    asyncio.run(main())
