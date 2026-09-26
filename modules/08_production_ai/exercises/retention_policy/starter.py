"""Compute deletion candidates using explicit time and legal-hold policy inputs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RetentionRecord:
    record_id: str
    created_at: datetime
    legal_hold: bool


def plan_retention(
    records: tuple[RetentionRecord, ...], now: datetime, retention_days: int
) -> tuple[str, ...]:
    """Validate all records and return oldest-first eligible IDs without side effects."""
    # TODO: Compare absolute instants, protect held records, and apply a strict cutoff.
    raise NotImplementedError("Implement library record retention planning")
