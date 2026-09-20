"""Student boundary for filtering and projecting event rows."""

from collections.abc import Iterable
from typing import TypedDict


class EventRow(TypedDict):
    """An event accepted by the filtering boundary."""

    id: str
    type: str
    active: bool


def active_event_ids(events: Iterable[EventRow], allowed_types: set[str]) -> list[str]:
    """Return active event IDs for allowed event types in input order."""
    event_rows = list(events)
    for event in event_rows:
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event ID must be a nonblank string")
        if not isinstance(event.get("type"), str):
            raise ValueError("event type must be a string")
        if not isinstance(event.get("active"), bool):
            raise ValueError("event active flag must be a boolean")

    raise NotImplementedError("filter and project active events")
