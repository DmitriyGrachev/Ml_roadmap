"""Fetch independent, mocked metadata concurrently with asyncio.gather."""

import asyncio


async def mocked_metadata_call(topic: str) -> str:
    await asyncio.sleep(0)
    return f"{topic}:ready"


async def collect_metadata(topics: list[str]) -> list[str]:
    return list(await asyncio.gather(*(mocked_metadata_call(topic) for topic in topics)))


def main() -> None:
    print(", ".join(asyncio.run(collect_metadata(["safety", "finance"]))))


if __name__ == "__main__":
    main()
