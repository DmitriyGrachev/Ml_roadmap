"""Independent learner SQL transactions, replay and mandatory saved run."""

import sqlite3
from typing import Any

import pytest

from roadmap_tools import exercise_call

from . import demo, starter
from .evidence import required_evidence, validate_pipeline

EVENTS: list[tuple[Any, ...]] = [
    ("x1", "notice", 15, " CIRCLE ", "circle"),
    ("x2", "notice", 30, "TRIANGLE", "triangle"),
    ("x2", "notice", 30, "TRIANGLE", "triangle"),
    ("x3", "late", 2, "SQUARE", "square"),
    ("x4", "notice", 1, "old circle", "circle"),
    ("x5", "bad", 40, " ", "circle"),
]


def seeded() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    exercise_call(starter.initialize, db)
    with db:
        db.executemany(
            "INSERT INTO raw_events(event_id,doc_id,event_time,text,label) VALUES (?,?,?,?,?)",
            EVENTS,
        )
    return db


@pytest.mark.student_exercise
def test_learner_increment_is_bounded_idempotent_and_late_safe() -> None:
    db = seeded()
    try:
        result = exercise_call(starter.load_increment, db, limit=2)
        assert result["extracted"] == 2
        assert result["watermark"] == 2
        assert starter.load_increment(db, limit=2)["duplicates"] == 1
        starter.load_increment(db, limit=2)
        rows = db.execute("SELECT doc_id,event_time,text FROM documents ORDER BY doc_id").fetchall()
        assert rows == [("late", 2, "square"), ("notice", 30, "triangle")]
        assert db.execute("SELECT COUNT(*) FROM quarantine").fetchone() == (1,)
        before = exercise_call(starter.snapshot, db)
        assert before == demo.snapshot(db)
        assert starter.load_increment(db)["extracted"] == 0
        assert starter.snapshot(db) == before
    finally:
        db.close()


@pytest.mark.student_exercise
def test_learner_trigger_failure_rolls_back_batch_and_cursor() -> None:
    db = seeded()
    try:
        db.executescript("""CREATE TRIGGER fail_notice BEFORE UPDATE ON documents
        BEGIN SELECT RAISE(ABORT, 'worker failed'); END;""")
        with pytest.raises(sqlite3.IntegrityError, match="worker failed"):
            exercise_call(starter.load_increment, db, limit=2)
        assert db.execute("SELECT value FROM cursor").fetchone() == (0,)
        assert db.execute("SELECT COUNT(*) FROM documents").fetchone() == (0,)
        assert db.execute("SELECT COUNT(*) FROM processed").fetchone() == (0,)
    finally:
        db.close()


@pytest.mark.student_exercise
def test_required_saved_learner_sql_replay() -> None:
    root = exercise_call(required_evidence)
    assert exercise_call(validate_pipeline, root)["mechanical_status"] == "VERIFIED"
