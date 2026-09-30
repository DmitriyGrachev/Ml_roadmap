"""Small, deterministic SQLite data for the analytics exercise."""

from pathlib import Path
from sqlite3 import Connection, connect


def create_connection(path: Path) -> Connection:
    """Create a new local database with event and support records."""
    if path.exists():
        raise FileExistsError(path)

    connection = connect(path)
    connection.executescript(
        """
        CREATE TABLE events (
            event_id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            occurred_at TEXT NOT NULL
        );
        CREATE TABLE support_tickets (
            ticket_id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL,
            status TEXT NOT NULL
        );
        """
    )
    connection.executemany(
        "INSERT INTO events VALUES (?, ?, ?, ?)",
        [
            (1, "u1", "view", "2026-09-02T08:00:00Z"),
            (2, "u1", "purchase", "2026-09-03T10:00:00Z"),
            (3, "u1", "view", "2026-09-03T10:00:00Z"),
            (4, "u2", "view", "2026-09-04T09:00:00Z"),
            (5, "u2", "purchase", "2026-09-04T11:00:00Z"),
            (6, "u3", "view", "2026-09-05T12:00:00Z"),
            (7, "u4", "purchase", "2026-09-08T00:00:00Z"),
            (8, "u5", "purchase", "2026-09-01T00:00:00Z"),
        ],
    )
    connection.executemany(
        "INSERT INTO support_tickets VALUES (?, ?, ?)",
        [
            (101, "u1", "open"),
            (102, "u1", "closed"),
            (103, "u2", "open"),
            (104, "orphan", "open"),
        ],
    )
    connection.commit()
    return connection
