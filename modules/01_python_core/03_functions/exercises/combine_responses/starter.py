"""Student boundary for aligning providers with one-shot response iterables."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    """A response returned by one payment provider."""

    reference: str
    status: str


@dataclass(frozen=True, slots=True)
class IndexedProviderResponse:
    """A provider response enriched with its original name and position."""

    index: int
    provider_name: str
    response: ProviderResponse


def combine_provider_responses(
    provider_names: Sequence[str],
    responses: Iterable[ProviderResponse],
) -> list[IndexedProviderResponse]:
    """Combine names and responses in order, requiring equal lengths.

    Raise:
        ValueError: If the two inputs contain different numbers of items.
    """
    raise NotImplementedError("combine provider names and responses")
