"""Independent parcel lookup; never imports the student analytics query."""

from dataclasses import dataclass
from sqlite3 import Connection, connect, sqlite_version
from statistics import median
from time import perf_counter
from typing import cast

QUERY = "SELECT parcel_id, weight FROM parcels WHERE zone = ? ORDER BY parcel_id"


@dataclass
class Experiment:
    before_rows: list[tuple[int, int]]
    after_rows: list[tuple[int, int]]
    before_plan: list[str]
    after_plan: list[str]
    before_ms: list[float]
    after_ms: list[float]
    index_pages: int
    page_bytes: int


def measure(
    connection: Connection, zone: str, repeats: int
) -> tuple[list[tuple[int, int]], list[float]]:
    rows = cast(list[tuple[int, int]], connection.execute(QUERY, (zone,)).fetchall())
    durations = []
    for _ in range(repeats):
        started = perf_counter()
        current = connection.execute(QUERY, (zone,)).fetchall()
        durations.append((perf_counter() - started) * 1000)
        if current != rows:
            raise AssertionError("rows changed during timing")
    return rows, durations


def run_experiment(size: int = 20_000, repeats: int = 7, zone: str = "Z017") -> Experiment:
    connection = connect(":memory:")
    try:
        connection.execute(
            "CREATE TABLE parcels (parcel_id INTEGER PRIMARY KEY, zone TEXT NOT NULL, "
            "weight INTEGER NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO parcels VALUES (?, ?, ?)",
            ((number, f"Z{number % 1000:03d}", number % 10) for number in range(size)),
        )
        connection.commit()
        before_plan = [row[3] for row in connection.execute("EXPLAIN QUERY PLAN " + QUERY, (zone,))]
        before_rows, before_ms = measure(connection, zone, repeats)
        before_pages = connection.execute("PRAGMA page_count").fetchone()[0]
        connection.execute("CREATE INDEX idx_parcels_zone ON parcels(zone)")
        connection.commit()
        after_plan = [row[3] for row in connection.execute("EXPLAIN QUERY PLAN " + QUERY, (zone,))]
        after_rows, after_ms = measure(connection, zone, repeats)
        if before_rows != after_rows:
            raise AssertionError("index experiment changed ordered rows")
        return Experiment(
            before_rows,
            after_rows,
            before_plan,
            after_plan,
            before_ms,
            after_ms,
            connection.execute("PRAGMA page_count").fetchone()[0] - before_pages,
            connection.execute("PRAGMA page_size").fetchone()[0],
        )
    finally:
        connection.close()


def main() -> None:
    result = run_experiment()
    print(f"SQLite {sqlite_version}; 20000 parcels; zone Z017; 7 warm samples per phase")
    print(f"before plan: {result.before_plan}")
    print(f"after plan: {result.after_plan}")
    print(f"ordered rows identical: {result.before_rows == result.after_rows}")
    print(f"rows: {result.after_rows}")
    print(f"before ms: {[round(value, 4) for value in result.before_ms]}")
    print(f"after ms: {[round(value, 4) for value in result.after_ms]}")
    print(f"median ms: {median(result.before_ms):.4f} -> {median(result.after_ms):.4f}")
    print(f"index allocation: +{result.index_pages} pages x {result.page_bytes} bytes")
    print("PostgreSQL: NOT_RUN")


if __name__ == "__main__":
    main()
