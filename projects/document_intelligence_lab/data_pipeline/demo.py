"""Author SQLite pipeline; ingestion cursor differs from event time. No cloud I/O."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path
from typing import Any

from ..artifacts import json_bytes
from ..contracts import normalize_document

EXTRACT_SQL = """SELECT ingest_id, event_id, doc_id, event_time, text, label
FROM raw_events WHERE ingest_id > ? ORDER BY ingest_id LIMIT ?"""
EXAMPLE_EVENTS: list[dict[str, Any]] = [
    {"event_id": "e1", "doc_id": "a", "event_time": 10, "text": "old circle", "label": "circle"},
    {
        "event_id": "e2",
        "doc_id": "a",
        "event_time": 20,
        "text": "new triangle",
        "label": "triangle",
    },
    {
        "event_id": "e2",
        "doc_id": "a",
        "event_time": 20,
        "text": "new triangle",
        "label": "triangle",
    },
    {"event_id": "e3", "doc_id": "b", "event_time": 5, "text": " late  SQUARE ", "label": "square"},
    {"event_id": "e4", "doc_id": "a", "event_time": 1, "text": "stale circle", "label": "circle"},
    {"event_id": "e5", "doc_id": "c", "event_time": 30, "text": "  ", "label": "circle"},
    {"event_id": "e6", "doc_id": "d", "event_time": -1, "text": "triangle", "label": "unknown"},
]


def initialize(db: sqlite3.Connection) -> None:
    db.executescript("""
    CREATE TABLE raw_events (
      ingest_id INTEGER PRIMARY KEY, event_id TEXT, doc_id TEXT,
      event_time INTEGER, text TEXT, label TEXT);
    CREATE TABLE documents (
      doc_id TEXT PRIMARY KEY, event_time INTEGER NOT NULL, ingest_id INTEGER NOT NULL,
      text TEXT NOT NULL, label TEXT NOT NULL);
    CREATE TABLE processed (event_id TEXT PRIMARY KEY, payload_sha256 TEXT NOT NULL);
    CREATE TABLE quarantine (ingest_id INTEGER PRIMARY KEY, reason TEXT NOT NULL);
    CREATE TABLE cursor (singleton INTEGER PRIMARY KEY CHECK(singleton=1), value INTEGER);
    INSERT INTO cursor VALUES (1, 0);
    """)


def append_events(db: sqlite3.Connection, events: list[dict[str, Any]]) -> None:
    with db:
        db.executemany(
            "INSERT INTO raw_events(event_id, doc_id, event_time, text, label) VALUES (?,?,?,?,?)",
            [(e["event_id"], e["doc_id"], e["event_time"], e["text"], e["label"]) for e in events],
        )


def load_increment(db: sqlite3.Connection, *, limit: int = 100) -> dict[str, int]:
    """Atomic single-writer batch: rows, dedup, quarantine and cursor commit together.

    This compact contract assumes immutable append-only source and one worker;
    PostgreSQL concurrency requires row locking/claiming, not blind reuse.
    """
    if type(limit) is not int or not 1 <= limit <= 10000:
        raise ValueError("limit must be integer in 1..10000")
    counts = {"extracted": 0, "duplicates": 0, "quarantined": 0, "upserted": 0}
    with db:
        # Explicit BEGIN also protects the first SELECT; rollback covers every target write.
        db.execute("BEGIN IMMEDIATE")
        watermark = db.execute("SELECT value FROM cursor WHERE singleton=1").fetchone()[0]
        rows = db.execute(EXTRACT_SQL, (watermark, limit)).fetchall()
        for seq, event_id, doc_id, event_time, text, label in rows:
            counts["extracted"] += 1
            payload = {"doc_id": doc_id, "event_time": event_time, "text": text, "label": label}
            digest = hashlib.sha256(json_bytes(payload)).hexdigest()
            reason = None
            previous = db.execute(
                "SELECT payload_sha256 FROM processed WHERE event_id=?", (event_id,)
            ).fetchone()
            if previous:
                if previous[0] == digest:
                    counts["duplicates"] += 1
                    watermark = seq
                    continue
                reason = "conflicting event_id"
            elif (
                not isinstance(event_id, str)
                or not event_id.strip()
                or not isinstance(doc_id, str)
                or not doc_id.strip()
                or type(event_time) is not int
                or event_time < 0
                or not isinstance(text, str)
                or not text.strip()
                or len(text) > 10000
                or label not in ("circle", "square", "triangle")
            ):
                reason = "invalid identity/time/text/label"
            if reason:
                db.execute("INSERT INTO quarantine VALUES (?, ?)", (seq, reason))
                counts["quarantined"] += 1
            else:
                db.execute("INSERT INTO processed VALUES (?,?)", (event_id, digest))
                result = db.execute(
                    """
                    INSERT INTO documents VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(doc_id) DO UPDATE SET
                      event_time=excluded.event_time, ingest_id=excluded.ingest_id,
                      text=excluded.text, label=excluded.label
                    WHERE excluded.event_time > documents.event_time OR
                      (excluded.event_time = documents.event_time
                       AND excluded.ingest_id > documents.ingest_id)
                    """,
                    (doc_id, event_time, seq, normalize_document(text), label),
                )
                counts["upserted"] += result.rowcount
            watermark = seq
        db.execute("UPDATE cursor SET value=? WHERE singleton=1", (watermark,))
    return {**counts, "watermark": watermark}


def snapshot(db: sqlite3.Connection) -> dict[str, Any]:
    watermark = db.execute("SELECT value FROM cursor WHERE singleton=1").fetchone()[0]
    source = db.execute(EXTRACT_SQL, (0, watermark)).fetchall() if watermark else []
    rows = [
        dict(zip(("doc_id", "event_time", "ingest_id", "text", "label"), row, strict=True))
        for row in db.execute("SELECT * FROM documents ORDER BY doc_id")
    ]
    rejected = [list(row) for row in db.execute("SELECT * FROM quarantine ORDER BY ingest_id")]
    return {
        "schema_version": 1,
        "transform": "unicode-whitespace-v1/latest-event-time-v1",
        "extract_sql": EXTRACT_SQL,
        "watermark": watermark,
        "source_sha256": hashlib.sha256(json_bytes(source)).hexdigest(),
        "rows": rows,
        "rows_sha256": hashlib.sha256(json_bytes(rows)).hexdigest(),
        "quarantine": rejected,
        "quarantine_count": len(rejected),
    }


def run_demo(output: Path) -> Path:
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    db = sqlite3.connect(":memory:")
    replay = sqlite3.connect(":memory:")
    try:
        initialize(db)
        append_events(db, EXAMPLE_EVENTS)
        batches = []
        while (batch := load_increment(db, limit=2))["extracted"]:
            batches.append(batch)
        manifest = snapshot(db)
        initialize(replay)
        append_events(replay, EXAMPLE_EVENTS)
        load_increment(replay)
        if snapshot(replay) != manifest:
            raise RuntimeError("replay differs")
        (output / "events.json").write_bytes(json_bytes(EXAMPLE_EVENTS))
        (output / "manifest.json").write_bytes(json_bytes(manifest))
        (output / "run.json").write_bytes(
            json_bytes(
                {
                    "evidence_kind": "AUTHOR_SQLITE_DEMO",
                    "batches": batches,
                    "replay_equal": True,
                    "postgres": "NOT_RUN",
                    "cloud": "NOT_RUN",
                }
            )
        )
    finally:
        db.close()
        replay.close()
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    print(run_demo(parser.parse_args().output))
