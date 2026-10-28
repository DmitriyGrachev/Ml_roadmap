"""A changed real model must be replaced by the complete verified A bundle."""

from pathlib import Path

import pytest

from ..artifacts import read_json


def test_recovery_restarts_a_after_real_b_prediction_and_failed_startup(tmp_path: Path) -> None:
    from .recovery import run_recovery

    output = run_recovery(tmp_path / "run", samples=3)
    report = read_json(output / "recovery.json")
    assert [event["stage"] for event in report["events"]] == ["A", "B", "failure", "A-restored"]
    assert [event.get("predicted_label") for event in report["events"]] == [
        "circle",
        "triangle",
        None,
        "circle",
    ]
    assert report["events"][0]["bundle_sha256"] == report["events"][3]["bundle_sha256"]
    assert report["events"][0]["bundle_sha256"] != report["events"][1]["bundle_sha256"]
    assert report["events"][2]["error"]
    assert report["sample_count"] == 9
    assert report["unit"] == "seconds"
    assert report["memory_bytes"] is None
    assert len(report["requests"]) == 9
    # Startup replays predictions before readiness; inference is already warmed.
    assert all(row["condition"] == "warm_after_startup_replay" for row in report["requests"])
    assert sum(row["request_position"] == "first" for row in report["requests"]) == 3
    assert all(
        row["duration_seconds"] >= 0 and row["status_code"] == 200 for row in report["requests"]
    )
    assert (output / "timeline.svg").is_file()
    with pytest.raises(FileExistsError):
        run_recovery(output, samples=3)
