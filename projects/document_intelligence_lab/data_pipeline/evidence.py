"""Replay learner source in a fresh database; author artifacts earn no exercise credit."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from ..artifacts import file_sha256, read_json
from . import demo, starter


def required_evidence() -> Path:
    path = os.environ.get("ROADMAP_PIPELINE_EVIDENCE")
    if not path:
        raise NotImplementedError("Run learner SQL pipeline; set ROADMAP_PIPELINE_EVIDENCE")
    return Path(path)


def validate_pipeline(root: Path) -> dict[str, Any]:
    report = read_json(root / "run.json")
    events = read_json(root / "events.json")
    manifest = read_json(root / "manifest.json")
    if (
        type(report.get("schema_version")) is not int
        or report.get("schema_version") != 1
        or report.get("exercise_id") != "ml-data-pipeline"
        or report.get("evidence_kind") != "STUDENT_SQL_PIPELINE"
    ):
        raise ValueError("wrong pipeline identity/evidence kind")
    if report.get("code_sha256") != file_sha256(Path(__file__).with_name("starter.py")):
        raise ValueError("learner source hash differs")
    analysis = report.get("analysis", {})
    for key in (
        "watermark_late_data",
        "dedup_conflict",
        "transaction_failure",
        "replay",
        "parquet_arrow",
        "cloud_mapping",
    ):
        if not isinstance(analysis.get(key), str) or not analysis[key].strip():
            raise ValueError(f"required analysis missing: {key}")
    if not isinstance(events, list) or len(events) < 8 or events == demo.EXAMPLE_EVENTS:
        raise ValueError("independent source with at least 8 events required")
    _require_source_cases(events)
    expected_manifest, expected_batches = _replay(demo, events, limit=2)
    actual, batches = _replay(starter, events, limit=2)
    if (
        actual != expected_manifest
        or manifest != expected_manifest
        or batches != expected_batches
        or report.get("batches") != expected_batches
    ):
        raise ValueError("learner/saved manifest or batches differ from trusted SQL replay")
    fresh, _ = _replay(starter, events, limit=100)
    if fresh != expected_manifest:
        raise ValueError("learner fresh replay with changed batch size differs")
    return {"mechanical_status": "VERIFIED", "learner_mastery": "REQUIRES_REVIEW"}


def _replay(
    implementation: Any, events: list[dict[str, Any]], *, limit: int
) -> tuple[dict[str, Any], list[dict[str, int]]]:
    db = sqlite3.connect(":memory:")
    try:
        implementation.initialize(db)
        # Source insertion is scaffolding; every target/schema/manifest operation is learner code.
        demo.append_events(db, events)
        batches = []
        for _ in range(len(events) + 1):
            batch = implementation.load_increment(db, limit=limit)
            if not batch["extracted"]:
                break
            batches.append(batch)
        else:
            raise ValueError("learner cursor did not terminate within source-sized bound")
        manifest = implementation.snapshot(db)
        if not isinstance(manifest, dict) or not manifest:
            raise ValueError("learner manifest is empty or malformed")
        if implementation.load_increment(db, limit=limit)["extracted"] != 0:
            raise ValueError("learner empty rerun extracted rows")
        if implementation.snapshot(db) != manifest:
            raise ValueError("learner empty rerun changed manifest")
        return manifest, batches
    finally:
        db.close()


def _require_source_cases(events: list[dict[str, Any]]) -> None:
    seen: dict[str, dict[str, Any]] = {}
    latest: dict[str, int] = {}
    maximum = -1
    cases: set[str] = set()
    for event in events:
        event_id, doc_id = event["event_id"], event["doc_id"]
        previous = seen.get(event_id)
        if previous is not None:
            cases.add("duplicate" if previous == event else "conflicting payload")
            continue
        seen[event_id] = event
        text, stamp = event["text"], event["event_time"]
        if not isinstance(text, str) or not text.strip() or len(text) > 10000:
            cases.add("invalid text")
            continue
        if (
            not isinstance(event_id, str)
            or not event_id.strip()
            or not isinstance(doc_id, str)
            or not doc_id.strip()
            or type(stamp) is not int
            or stamp < 0
            or event["label"] not in ("circle", "square", "triangle")
        ):
            continue
        if doc_id not in latest and stamp < maximum:
            cases.add("late unseen document")
        if doc_id in latest and stamp < latest[doc_id]:
            cases.add("stale update")
        latest[doc_id] = max(stamp, latest.get(doc_id, -1))
        maximum = max(maximum, stamp)
    required = {
        "duplicate",
        "conflicting payload",
        "invalid text",
        "late unseen document",
        "stale update",
    }
    if missing := required - cases:
        raise ValueError("required source cases missing: " + ", ".join(sorted(missing)))
