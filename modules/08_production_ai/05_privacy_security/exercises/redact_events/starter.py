"""Student boundary for a small allowlisted telemetry schema."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

EVENT_NAMES = frozenset({"request_completed", "cache_hit", "provider_error"})
ROUTES = frozenset({"/books", "/labels"})


@dataclass(frozen=True)
class RedactedEvent:
    safe: dict[str, object]
    dropped_fields: int


def redact_events(events: Sequence[Mapping[str, object]]) -> tuple[RedactedEvent, ...]:
    """Validate known fields and copy only the README's explicit event allowlist."""
    # TODO: project top-level and attribute fields, count omissions, and copy output.
    raise NotImplementedError("minimize structured events")
