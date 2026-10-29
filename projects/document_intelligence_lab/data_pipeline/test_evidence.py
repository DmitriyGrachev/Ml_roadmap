"""Test-owned artifacts exercise replay validation; no learner submission is saved."""

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from ..artifacts import file_sha256, json_bytes, read_json
from . import demo, starter
from .evidence import required_evidence, validate_pipeline


@pytest.fixture
def evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for name in ("initialize", "load_increment", "snapshot"):
        monkeypatch.setattr(starter, name, getattr(demo, name))
    events = [dict(e) for e in demo.EXAMPLE_EVENTS]
    events[0]["text"] = "independent old circle"
    events.append(
        {
            "event_id": "e2",
            "doc_id": "a",
            "event_time": 20,
            "text": "conflicting triangle",
            "label": "triangle",
        }
    )
    db = sqlite3.connect(":memory:")
    try:
        demo.initialize(db)
        demo.append_events(db, events)
        batches = []
        while (batch := demo.load_increment(db, limit=2))["extracted"]:
            batches.append(batch)
        manifest = demo.snapshot(db)
    finally:
        db.close()
    report: dict[str, Any] = {
        "schema_version": 1,
        "exercise_id": "ml-data-pipeline",
        "evidence_kind": "STUDENT_SQL_PIPELINE",
        "batches": batches,
        "code_sha256": file_sha256(Path(__file__).with_name("starter.py")),
        "analysis": {
            key: "Test-owned synthetic artifact; no learner claim."
            for key in (
                "watermark_late_data",
                "dedup_conflict",
                "transaction_failure",
                "replay",
                "parquet_arrow",
                "cloud_mapping",
            )
        },
    }
    for name, value in (("events", events), ("manifest", manifest), ("run", report)):
        (tmp_path / f"{name}.json").write_bytes(json_bytes(value))
    return tmp_path


def test_independent_source_replays_and_gate_preserves_human_review(evidence: Path) -> None:
    assert validate_pipeline(evidence) == {
        "mechanical_status": "VERIFIED",
        "learner_mastery": "REQUIRES_REVIEW",
    }


@pytest.mark.parametrize("change", ["author", "source", "rows", "counts"])
def test_altered_artifacts_are_rejected(evidence: Path, change: str) -> None:
    name = "manifest" if change == "rows" else "run"
    path = evidence / f"{name}.json"
    value = read_json(path)
    if change == "author":
        value["evidence_kind"] = "AUTHOR_SQLITE_DEMO"
    elif change == "source":
        value["code_sha256"] = "0" * 64
    elif change == "rows":
        value["rows"][0]["text"] = "fabricated"
    else:
        value["batches"][0]["extracted"] = 999
    path.write_bytes(json_bytes(value))
    with pytest.raises(ValueError, match=r"identity|source|replay"):
        validate_pipeline(evidence)


def test_missing_artifact_is_an_unfinished_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROADMAP_PIPELINE_EVIDENCE", raising=False)
    with pytest.raises(NotImplementedError, match="Run learner SQL"):
        required_evidence()


@pytest.mark.parametrize("value", [{}, {"rows": []}])
def test_broken_learner_snapshot_cannot_borrow_author_manifest(
    evidence: Path, monkeypatch: pytest.MonkeyPatch, value: dict[str, Any]
) -> None:
    monkeypatch.setattr(starter, "snapshot", lambda db: value)
    with pytest.raises(ValueError, match="learner"):
        validate_pipeline(evidence)


@pytest.mark.parametrize("missing", ["conflict", "late-unseen", "invalid-text", "stale"])
def test_source_case_categories_are_required_separately(evidence: Path, missing: str) -> None:
    events = read_json(evidence / "events.json")
    if missing == "conflict":
        events[-1] = {
            "event_id": "new",
            "doc_id": "extra",
            "event_time": 50,
            "text": "triangle",
            "label": "triangle",
        }
    elif missing == "late-unseen":
        events[3]["event_time"] = 50
    elif missing == "invalid-text":
        events[5]["text"] = "valid circle"
    else:
        events[4]["event_time"] = 30
    (evidence / "events.json").write_bytes(json_bytes(events))
    with pytest.raises(ValueError, match="required source cases missing"):
        validate_pipeline(evidence)
