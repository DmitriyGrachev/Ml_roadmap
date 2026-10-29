"""Student transfer: first successful replica, with bounded owned work."""

from collections.abc import Awaitable, Callable, Sequence


async def first_healthy(
    replicas: Sequence[str],
    probe: Callable[[str], Awaitable[str]],
    limit: int,
    timeout: float | None = None,
) -> str:
    """Return the first success; await loser cleanup; fail if no replica succeeds."""
    # TODO: tolerate individual Exception failures; propagate external cancellation.
    raise NotImplementedError("race replicas with bounded concurrency and complete cleanup")
