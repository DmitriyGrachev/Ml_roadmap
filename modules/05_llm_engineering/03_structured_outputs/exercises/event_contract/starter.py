"""Validate an extracted museum event against application-owned evidence."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Event(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    title: str
    venue: str
    starts_at: datetime
    ends_at: datetime
    seats: int = Field(ge=0, le=200)
    evidence: str


def parse_event(payload: str, allowed_venues: frozenset[str], source_text: str) -> Event:
    """Parse strict JSON, then enforce the semantic contract in README.md."""
    raise NotImplementedError("Implement museum event validation")
