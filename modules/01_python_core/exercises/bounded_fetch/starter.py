"""Student boundary for bounded station lookups with injected asynchronous I/O."""

from collections.abc import Awaitable, Callable, Sequence


async def fetch_bounded(
    keys: Sequence[str], fetch: Callable[[str], Awaitable[str]], limit: int
) -> list[str]:
    """Fetch once per occurrence, cap active calls, and preserve the input order."""
    # TODO: bound active calls; on failure cancel and await remaining work, then re-raise.
    raise NotImplementedError("bound concurrent station fetches")
