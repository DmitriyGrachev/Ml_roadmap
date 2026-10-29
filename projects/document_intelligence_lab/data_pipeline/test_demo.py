"""Behavioral contracts: ingestion order, transaction safety and reproducible replay."""

import sqlite3

import pytest

from . import demo


def test_incremental_late_duplicate_invalid_and_replay() -> None:
    db = sqlite3.connect(":memory:")
    demo.initialize(db)
    demo.append_events(db, demo.EXAMPLE_EVENTS)
    first = demo.load_increment(db, limit=2)
    assert first["watermark"] == 2
    while demo.load_increment(db, limit=2)["extracted"]:
        pass
    manifest = demo.snapshot(db)
    assert [(r["doc_id"], r["event_time"], r["text"]) for r in manifest["rows"]] == [
        ("a", 20, "new triangle"),
        ("b", 5, "late square"),
    ]
    assert manifest["quarantine_count"] == 2
    assert manifest["watermark"] == len(demo.EXAMPLE_EVENTS)
    assert demo.load_increment(db)["extracted"] == 0
    assert demo.snapshot(db) == manifest
    replay = sqlite3.connect(":memory:")
    demo.initialize(replay)
    demo.append_events(replay, demo.EXAMPLE_EVENTS)
    demo.load_increment(replay)
    assert demo.snapshot(replay) == manifest


def test_transaction_rolls_back_rows_and_watermark(monkeypatch: pytest.MonkeyPatch) -> None:
    db = sqlite3.connect(":memory:")
    demo.initialize(db)
    demo.append_events(db, demo.EXAMPLE_EVENTS[:2])

    def broken(text: str) -> str:
        if "new" in text:
            raise RuntimeError("interrupted worker")
        return text

    monkeypatch.setattr(demo, "normalize_document", broken)
    with pytest.raises(RuntimeError, match="interrupted"):
        demo.load_increment(db)
    assert demo.snapshot(db)["watermark"] == 0
    assert demo.snapshot(db)["rows"] == []
    assert db.execute("SELECT COUNT(*) FROM processed").fetchone() == (0,)


def test_conflicting_duplicate_and_parameterized_document_identity() -> None:
    db = sqlite3.connect(":memory:")
    demo.initialize(db)
    demo.append_events(
        db,
        [
            {
                "event_id": "e",
                "doc_id": "'; DROP TABLE documents;--",
                "event_time": 2,
                "text": "  TRIANGLE  ",
                "label": "triangle",
            },
            {
                "event_id": "e",
                "doc_id": "other",
                "event_time": 3,
                "text": "changed",
                "label": "circle",
            },
        ],
    )
    result = demo.load_increment(db)
    assert result["quarantined"] == 1
    assert demo.snapshot(db)["rows"][0]["text"] == "triangle"


@pytest.mark.parametrize("limit", [0, -1, True, 10001])
def test_bounded_batch(limit: int) -> None:
    db = sqlite3.connect(":memory:")
    demo.initialize(db)
    with pytest.raises(ValueError, match="limit"):
        demo.load_increment(db, limit=limit)
