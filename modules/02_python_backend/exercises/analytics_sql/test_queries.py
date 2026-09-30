"""Local fixture checks and result-based SQL exercise assertions."""

from pathlib import Path

import pytest


def test_fixture_preserves_ties_duplicates_and_missing_keys(tmp_path: Path) -> None:
    from .fixtures import create_connection

    database_path = tmp_path / "analytics.sqlite3"
    connection = create_connection(database_path)
    try:
        assert database_path.is_file()
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone() == (8,)
        assert connection.execute("SELECT COUNT(*) FROM support_tickets").fetchone() == (4,)
        assert connection.execute(
            "SELECT event_id, event_type FROM events WHERE user_id = 'u1' "
            "AND occurred_at = '2026-09-03T10:00:00Z' ORDER BY event_id"
        ).fetchall() == [(2, "purchase"), (3, "view")]
        assert connection.execute(
            "SELECT COUNT(*) FROM support_tickets WHERE user_id = 'orphan'"
        ).fetchone() == (1,)
    finally:
        connection.close()


def test_tie_variation_rejects_opposite_tie_mutant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from . import test_starter as contract

    # Deliberately fixture-specific wrong query: other users' aggregates are fixed.
    # It chooses the smaller tied ID for u1; it is not a general exercise solution.
    wrong_query = """
    WITH wrong AS (
        SELECT event_type FROM events WHERE user_id = 'u1'
        ORDER BY occurred_at DESC, event_id ASC LIMIT 1
    )
    SELECT 'purchase', 2 + (event_type = 'purchase'),
           1 + 2 * (event_type = 'purchase'), 1 FROM wrong
    UNION ALL
    SELECT 'view', 1 + (event_type = 'view'), 2 * (event_type = 'view'), 1 FROM wrong
    """
    monkeypatch.setattr(contract, "analytics_query", lambda: wrong_query)
    with pytest.raises(AssertionError):
        contract.test_analytics_query_uses_event_id_for_timestamp_ties(tmp_path)
