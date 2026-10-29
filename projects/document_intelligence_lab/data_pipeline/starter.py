"""Independent SQL exercise. Do not import/call the author demo pipeline."""

import sqlite3
from typing import Any


def initialize(db: sqlite3.Connection) -> None:
    """Create raw_events/documents/processed/quarantine/cursor tables; see README."""
    raise NotImplementedError("Implement SQL schema and persistent ingestion cursor")


def load_increment(db: sqlite3.Connection, *, limit: int = 100) -> dict[str, int]:
    """Atomic bounded extraction, quality gate, dedup, latest-event upsert and cursor."""
    raise NotImplementedError("Implement incremental/idempotent SQL transaction")


def snapshot(db: sqlite3.Connection) -> dict[str, Any]:
    """Canonical rows, SQL, transform version, watermark, source/output hashes, rejects."""
    raise NotImplementedError("Implement deterministic reproducible manifest")
