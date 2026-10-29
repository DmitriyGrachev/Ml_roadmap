"""Learner behavior and mandatory saved measured TCP artifact are distinct gates."""

from pathlib import Path

import pytest

from roadmap_tools import exercise_call

from ..artifacts import file_sha256, read_json
from . import starter
from ._test_support import RecordingTransport, make_bundles
from .demo import STAGES
from .evidence import required_evidence, validate_lifecycle


@pytest.mark.student_exercise
def test_learner_summary_covers_failure_and_empty_success_set() -> None:
    rows = [
        {"outcome": "ok", "seconds": 0.2},
        {"outcome": "timeout", "seconds": 2.0},
        {"outcome": "http_error", "seconds": 0.1},
        {"outcome": "transport_error", "seconds": 0.3},
    ]
    result = exercise_call(starter.summarize_outcomes, rows)
    assert result == {
        "attempts": 4,
        "successes": 1,
        "failures": 3,
        "timeouts": 1,
        "http_errors": 1,
        "transport_errors": 1,
        "median_seconds": 0.2,
        "observed_max_seconds": 0.2,
    }
    empty = starter.summarize_outcomes(rows[1:])
    assert empty["median_seconds"] is None
    assert empty["observed_max_seconds"] is None


@pytest.mark.student_exercise
def test_learner_delayed_labels_use_availability_and_denominator() -> None:
    predictions = [
        {"request_id": "a", "prediction": "circle", "predicted_at": 10},
        {"request_id": "b", "prediction": "triangle", "predicted_at": 20},
    ]
    labels = [
        {"request_id": "a", "label": "square", "available_at": 30},
        {"request_id": "b", "label": "triangle", "available_at": 60},
    ]
    result = exercise_call(starter.join_delayed_labels, predictions, labels, as_of=40)
    assert result == {"labeled_count": 1, "coverage": 0.5, "accuracy": 0.0}
    assert starter.join_delayed_labels(predictions, labels, as_of=25)["accuracy"] is None


@pytest.mark.student_exercise
def test_required_measured_learner_tcp_evidence() -> None:
    root = exercise_call(required_evidence)
    assert validate_lifecycle(root)["mechanical_status"] == "VERIFIED"


@pytest.mark.student_exercise
def test_learner_runner_orchestrates_real_api_through_offline_transport(tmp_path: Path) -> None:
    bundles = make_bundles(tmp_path / "source")
    io = RecordingTransport()
    output = tmp_path / "learner"
    result = exercise_call(
        starter.run_lifecycle,
        bundles / "rules",
        bundles / "tfidf-linear",
        output,
        requests=6,
        concurrency=2,
        transport=io,
    )
    assert result == output
    report = read_json(output / "lifecycle.json")
    assert report["run_status"] == "COMPLETE"
    assert [e["stage"] for e in report["events"]] == list(STAGES)
    assert len(io.closed) == 5
    assert len(io.calls) == 5
    assert [c["count"] for c in io.loads] == [6] * 4
    assert [c["concurrency"] for c in io.loads] == [2] * 4
    assert [c["digest"] for c in io.calls[:3]] == [
        file_sha256(bundles / method / "manifest.json")
        for method in ("rules", "rules", "tfidf-linear")
    ]
    assert io.calls[3]["digest"] != file_sha256(bundles / "tfidf-linear" / "manifest.json")
    assert io.calls[4]["digest"] == io.calls[0]["digest"]
    assert sum(r["payload"] == {"text": " "} for r in io.requests) == 4
    assert sum(r["timeout"] < 0.01 for r in io.requests) == 4
    assert all(e["cleanup_exit_code"] is not None for e in report["events"])


@pytest.mark.student_exercise
def test_learner_runner_preserves_failure_and_cleans_child(tmp_path: Path) -> None:
    bundles = make_bundles(tmp_path / "source")
    io = RecordingTransport(fail_stage="B")
    output = tmp_path / "failed"
    with pytest.raises(RuntimeError, match=r"warm|load|request"):
        exercise_call(
            starter.run_lifecycle,
            bundles / "rules",
            bundles / "tfidf-linear",
            output,
            requests=6,
            concurrency=2,
            transport=io,
        )
    report = read_json(output / "lifecycle.json")
    assert report["run_status"] == "FAILED"
    assert len(report["events"]) == 3
    stage = report["events"][-1]
    assert stage["summary"]["attempts"] == 6
    assert stage["summary"]["timeouts"] == 1
    assert stage["cleanup_exit_code"] is not None
    assert len(io.closed) == 3
