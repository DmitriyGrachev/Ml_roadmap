"""Fetch independent, mocked metadata concurrently with asyncio.gather."""

import asyncio
from collections.abc import Awaitable, Callable

type MetadataFetcher = Callable[[str], Awaitable[str]]


async def mocked_metadata_call(topic: str) -> str:
    await asyncio.sleep(0)
    return f"{topic}:ready"


async def collect_metadata(
    topics: list[str], fetch: MetadataFetcher = mocked_metadata_call
) -> list[str]:
    return list(await asyncio.gather(*(fetch(topic) for topic in topics)))


def main() -> None:
    print(", ".join(asyncio.run(collect_metadata(["safety", "finance"]))))


if __name__ == "__main__":
    main()
