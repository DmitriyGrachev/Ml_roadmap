"""Student boundary for concurrent quote fan-out."""

from collections.abc import Awaitable, Callable, Sequence
from decimal import Decimal

type QuoteFetcher = Callable[[str], Awaitable[Decimal]]


async def fetch_quotes(
    symbols: Sequence[str],
    fetcher: QuoteFetcher,
) -> list[Decimal]:
    """Fetch all symbols concurrently and preserve the input order."""
    raise NotImplementedError("fetch quotes concurrently")
