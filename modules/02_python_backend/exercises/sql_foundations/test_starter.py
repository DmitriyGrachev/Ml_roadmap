"""Execute student SQL on distinct datasets instead of checking SQL source text."""

import sqlite3

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import latest_valid_measurements_sql

pytestmark = pytest.mark.student_exercise


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        (
            [
                (1, "A", "2026-01-01", 2.0),
                (2, "A", "2026-01-02", None),
                (3, "B", "2026-01-01", 4.0),
                (4, "B", "2026-01-01", 5.0),
                (5, "C", "2026-01-03", None),
            ],
            [("A", 1, 2.0), ("B", 4, 5.0)],
        ),
        (
            [
                (8, "Z", "2026-03-01", 0.0),
                (2, "Z", "2026-03-02", -3.0),
                (7, "D", "2026-04-01", 9.0),
            ],
            [("D", 7, 9.0), ("Z", 2, -3.0)],
        ),
        ([(1, "A", "2026-01-01", 0.0)], [("A", 1, 0.0)]),
        ([], []),
        ([(1, "A", "2026-01-01", None)], []),
    ],
)
def test_latest_nonnull_is_selected_before_ranking(
    rows: list[tuple[int, str, str, float | None]], expected: list[tuple[str, int, float]]
) -> None:
    query = exercise_call(latest_valid_measurements_sql)
    with sqlite3.connect(":memory:") as connection:
        connection.execute(
            "CREATE TABLE measurements (id INTEGER PRIMARY KEY, device TEXT NOT NULL, "
            "measured_at TEXT NOT NULL, value REAL)"
        )
        connection.executemany("INSERT INTO measurements VALUES (?, ?, ?, ?)", rows)
        assert connection.execute(query).fetchall() == expected
        assert connection.execute("SELECT COUNT(*) FROM measurements").fetchone() == (len(rows),)
