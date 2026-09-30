"""Check SQL results on real local SQLite connections, not query spelling."""

from pathlib import Path

import pytest

from roadmap_tools.exercise import exercise_call

from .fixtures import create_connection
from .starter import analytics_query

pytestmark = pytest.mark.student_exercise


def test_analytics_query_handles_latest_event_ties_and_support_cardinality(tmp_path: Path) -> None:
    connection = create_connection(tmp_path / "base.sqlite3")
    try:
        rows = connection.execute(exercise_call(analytics_query)).fetchall()
        assert rows == [("purchase", 2, 1, 1), ("view", 2, 2, 1)]
    finally:
        connection.close()


def test_analytics_query_uses_current_rows_after_fixture_changes(tmp_path: Path) -> None:
    connection = create_connection(tmp_path / "changed.sqlite3")
    try:
        connection.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?)",
            (9, "u6", "view", "2026-09-06T10:00:00Z"),
        )
        connection.execute("INSERT INTO support_tickets VALUES (?, ?, ?)", (105, "u6", "open"))
        rows = connection.execute(exercise_call(analytics_query)).fetchall()
        assert rows == [("purchase", 2, 1, 1), ("view", 3, 3, 1)]
    finally:
        connection.close()


def test_analytics_query_uses_event_id_for_timestamp_ties(tmp_path: Path) -> None:
    connection = create_connection(tmp_path / "tie.sqlite3")
    try:
        connection.execute("UPDATE events SET event_type = 'view' WHERE event_id = 2")
        connection.execute("UPDATE events SET event_type = 'purchase' WHERE event_id = 3")
        rows = connection.execute(exercise_call(analytics_query)).fetchall()
        assert rows == [("purchase", 3, 3, 1), ("view", 1, 0, 1)]
    finally:
        connection.close()
