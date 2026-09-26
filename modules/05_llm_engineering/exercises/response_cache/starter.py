"""Student boundary for a deterministic in-memory response-cache transition."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class CacheKey:
    """All response-affecting key components in this simplified exercise."""

    prompt: str
    model: str
    prompt_version: str


@dataclass(frozen=True)
class CacheEntry:
    """An immutable response and absolute expiry."""

    key: CacheKey
    response: str
    expires_at: float


@dataclass(frozen=True)
class CacheResult:
    """New cache snapshot, returned response, and whether a read hit."""

    entries: tuple[CacheEntry, ...]
    response: str | None
    hit: bool


def cache_response(
    entries: tuple[CacheEntry, ...],
    key: CacheKey,
    *,
    now: float,
    ttl: float,
    response: str | None = None,
) -> CacheResult:
    """Read or write one key and prune expired entries using injected time."""
    for value in (now, ttl):
        if type(value) not in (int, float) or not isfinite(value):
            raise ValueError("now and ttl must be finite numbers")
    if now < 0 or ttl <= 0 or not isfinite(now + ttl):
        raise ValueError("now must be nonnegative and ttl positive with finite sum")
    keys: set[CacheKey] = set()
    for item_key in (key, *(entry.key for entry in entries)):
        if any(
            not isinstance(part, str) or not part.strip()
            for part in (item_key.prompt, item_key.model, item_key.prompt_version)
        ):
            raise ValueError("cache key components must be nonblank strings")
    for entry in entries:
        if entry.key in keys:
            raise ValueError("cache entries must have unique keys")
        if not isinstance(entry.response, str):
            raise ValueError("cached responses must be strings")
        if type(entry.expires_at) not in (int, float) or not isfinite(entry.expires_at):
            raise ValueError("expiry must be finite")
        if entry.expires_at < 0:
            raise ValueError("expiry must be nonnegative")
        keys.add(entry.key)
    if response is not None and not isinstance(response, str):
        raise ValueError("response must be a string or None")
    # TODO: prune, read or replace, and return a new immutable snapshot.
    raise NotImplementedError("versioned response cache")
