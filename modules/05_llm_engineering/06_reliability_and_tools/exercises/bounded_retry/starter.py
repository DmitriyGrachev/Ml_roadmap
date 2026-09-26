"""Retry a museum-label provider at one explicit application boundary."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Request:
    prompt: str
    idempotency_key: str


class TransientError(RuntimeError):
    """An adapter-classified temporary provider failure."""


class PermanentError(RuntimeError):
    """A failure that retries cannot fix, such as an invalid credential."""


class Provider(Protocol):
    def complete(self, request: Request) -> str:
        """Return text or raise an adapter-classified error."""
        ...


def invoke_with_retry(
    provider: Provider,
    request: Request,
    max_attempts: int,
    delays: tuple[float, ...],
    sleep: Callable[[float], None],
) -> str:
    """Use bounded retries and one stable request according to README.md."""
    raise NotImplementedError("Implement the bounded provider retry boundary")
