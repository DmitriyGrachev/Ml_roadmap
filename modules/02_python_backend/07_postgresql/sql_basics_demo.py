"""Offline SQLite SQL teaching trace. PostgreSQL and containers are separate runtime checks."""

import json
import sqlite3

QUERIES = {
    "filtered": """
        SELECT r.id, s.name, r.value FROM readings r JOIN stations s ON s.id = r.station_id
        WHERE r.value IS NOT NULL ORDER BY r.value DESC, r.id
    """,
    "null_equals": "SELECT id FROM readings WHERE value = NULL ORDER BY id",
    "null_is": "SELECT id FROM readings WHERE value IS NULL ORDER BY id",
    "grouped": """
        SELECT s.name, COUNT(r.id), COUNT(r.value), SUM(r.value)
        FROM stations s LEFT JOIN readings r ON r.station_id = s.id
        GROUP BY s.id, s.name ORDER BY s.name
    """,
    "having": """
        SELECT s.name, AVG(r.value) FROM stations s
        JOIN readings r ON r.station_id = s.id
        GROUP BY s.id, s.name HAVING AVG(r.value) >= 10 ORDER BY s.name
    """,
    "joined": """
        SELECT r.id, t.tag FROM readings r JOIN tags t ON t.station_id = r.station_id
        ORDER BY r.id, t.tag
    """,
    "windowed": """
        SELECT r.id, s.name, r.value,
          ROW_NUMBER() OVER (
            PARTITION BY s.id ORDER BY r.value DESC NULLS LAST, r.id
          ) AS position,
          DENSE_RANK() OVER (
            PARTITION BY s.id ORDER BY r.value DESC NULLS LAST
          ) AS value_rank
        FROM readings r JOIN stations s ON s.id = r.station_id
        ORDER BY s.name, position
    """,
}


def run_demo() -> dict[str, list[tuple[object, ...]]]:
    with sqlite3.connect(":memory:") as connection:
        connection.executescript("""
            CREATE TABLE stations (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
            INSERT INTO stations VALUES (1, 'north'), (2, 'south'), (3, 'west');
            CREATE TABLE readings (id INTEGER PRIMARY KEY, station_id INTEGER, value INTEGER);
            INSERT INTO readings VALUES (1, 1, 8), (2, 1, NULL), (3, 2, 12), (4, 2, 12);
            CREATE TABLE tags (station_id INTEGER, tag TEXT);
            INSERT INTO tags VALUES (1, 'indoor'), (1, 'quiet'), (2, 'outdoor');
        """)
        return {name: connection.execute(query).fetchall() for name, query in QUERIES.items()}


def main() -> None:
    print(
        json.dumps(
            {"engine": "SQLite", "version": sqlite3.sqlite_version, "results": run_demo()},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
