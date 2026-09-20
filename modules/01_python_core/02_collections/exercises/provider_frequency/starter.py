"""Student boundary for counting payment-provider names."""

from collections.abc import Iterable


def provider_frequencies(providers: Iterable[str]) -> dict[str, int]:
    """Count provider names in first-seen order with case preserved."""
    raise NotImplementedError("count payment providers")
