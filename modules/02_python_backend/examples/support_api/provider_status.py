import asyncio
from collections.abc import Sequence
from typing import Protocol

from pydantic import BaseModel


class ProviderStatus(BaseModel):
    """Public availability reported by one support integration."""

    provider: str
    available: bool


class StatusProvider(Protocol):
    async def fetch_status(self) -> ProviderStatus: ...


async def fetch_provider_statuses(
    providers: Sequence[StatusProvider],
) -> list[ProviderStatus]:
    """Await independent provider I/O concurrently in configured order."""

    return list(await asyncio.gather(*(provider.fetch_status() for provider in providers)))
