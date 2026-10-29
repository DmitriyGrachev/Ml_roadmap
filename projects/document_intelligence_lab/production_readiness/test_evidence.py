"""Offline provenance boundaries; measured lifecycle validation runs explicitly."""

from pathlib import Path

import pytest

from ..artifacts import file_sha256, json_bytes, read_json
from .evidence import required_evidence, validate_lifecycle


def test_author_evidence_cannot_claim_learner_credit(tmp_path: Path) -> None:
    (tmp_path / "lifecycle.json").write_bytes(
        json_bytes(
            {
                "schema_version": 1,
                "exercise_id": "production-service-lifecycle",
                "evidence_kind": "AUTHOR_LOCAL_TCP_DEMO",
                "transport": "localhost TCP/uvicorn",
                "unit": "seconds",
                "device": "cpu",
            }
        )
    )
    with pytest.raises(ValueError, match="identity/evidence"):
        validate_lifecycle(tmp_path)


def test_missing_runtime_artifact_is_unfinished(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROADMAP_LIFECYCLE_EVIDENCE", raising=False)
    with pytest.raises(NotImplementedError, match="Run learner TCP"):
        required_evidence()


@pytest.fixture
def measured_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Synthetic I/O fixture tests schema/identities, not runtime transport credit.
    from ..part_a1 import demo as training
    from ._test_support import RecordingTransport, make_bundles
    from .demo import run_demo

    monkeypatch.setattr(training, "run_demo", make_bundles)
    return run_demo(
        tmp_path / "synthetic", requests=4, concurrency=2, transport=RecordingTransport()
    )


def test_complete_synthetic_contract_still_requires_human_review(measured_contract: Path) -> None:
    assert validate_lifecycle(measured_contract, learner=False) == {
        "mechanical_status": "VERIFIED",
        "learner_mastery": "REQUIRES_REVIEW",
    }


@pytest.mark.parametrize(
    "change",
    ["valid-rejected-digest", "model", "preprocessing", "shape", "wrong-log", "deadline-model"],
)
def test_bundle_identity_and_rejection_are_bound(measured_contract: Path, change: str) -> None:
    path = measured_contract / "lifecycle.json"
    report = read_json(path)
    if change == "valid-rejected-digest":
        report["events"][3]["bundle_sha256"] = report["bundles"]["B"]["manifest_sha256"]
    elif change == "deadline-model":
        report["events"][0]["fault_probes"][1]["payload"]["model_id"] = "nonexistent-model"
    elif change == "wrong-log":
        log = measured_contract / "rejected.log"
        log.write_text("ImportError: some unrelated startup failure", encoding="utf-8")
        report["events"][3]["startup_log"]["sha256"] = file_sha256(log)
    else:
        for event in report["events"]:
            if event["stage"] == "rejected":
                continue
            for row in [event["first_request"], *event["warm_requests"]]:
                if change == "model":
                    row["payload"]["model_id"] = "nonexistent-model"
                elif change == "preprocessing":
                    row["payload"]["preprocessing_version"] = 999
                else:
                    row["payload"]["unexpected"] = "field"
    path.write_bytes(json_bytes(report))
    with pytest.raises(ValueError, match=r"digest|identity|shape|startup log"):
        validate_lifecycle(measured_contract, learner=False)


def test_normal_load_failure_preserves_partial_measurements_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ..part_a1 import demo as training
    from ._test_support import RecordingTransport, make_bundles
    from .demo import run_demo

    monkeypatch.setattr(training, "run_demo", make_bundles)
    io = RecordingTransport(fail_stage="B")
    output = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="warm inference failed"):
        run_demo(output, requests=4, concurrency=2, transport=io)
    report = read_json(output / "lifecycle.json")
    assert report["run_status"] == "FAILED"
    assert "warm inference failed" in report["failure_reason"]
    assert [e["stage"] for e in report["events"]] == ["A", "A-restarted", "B"]
    stage = report["events"][-1]
    assert stage["summary"]["attempts"] == 4
    assert stage["summary"]["successes"] == 3
    assert stage["summary"]["timeouts"] == 1
    assert stage["warm_requests"][0]["outcome"] == "timeout"
    assert stage["fault_summary"]["attempts"] == 2
    assert stage["stage_status"] == "FAILED"
    assert stage["cleanup_exit_code"] == -15
    assert len(io.closed) == 3
    with pytest.raises(ValueError, match="failed or incomplete"):
        validate_lifecycle(output, learner=False)
