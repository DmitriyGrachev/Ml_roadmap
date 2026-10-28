"""Author checks for the bounded, offline Production AI teaching packet."""

import hashlib
import importlib
import importlib.metadata
import json
import platform
import socket
from copy import deepcopy
from pathlib import Path

import pytest

production = importlib.import_module("modules.08_production_ai.walkthrough")
agents = importlib.import_module("modules.07_agents.walkthrough")


@pytest.fixture(autouse=True)
def block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network connection attempted")

    monkeypatch.setattr(socket.socket, "connect", deny)


def test_window_uses_a_events_and_literal_arithmetic() -> None:
    packet = production.build_packet()
    events = packet["observed_events"]
    assert [row["run_id"] for row in events] == [
        "answer",
        "success",
        "denied",
        "refused",
        "cancelled",
        "failure_recovered",
        "attempt_exhausted",
        "unknown_after_effect",
    ]
    assert [row["simulated_request_latency_ms"] for row in events] == [
        10,
        20,
        10,
        10,
        10,
        30,
        20,
        20,
    ]
    assert [row["tool_attempt_events"] for row in events] == [0, 1, 0, 0, 0, 2, 1, 1]
    assert sum(row["authored_proposal_events"] for row in events) == 7
    assert all(row["real_model_calls"] == 0 for row in events)
    assert all(row["reference_label"] is None for row in events)
    assert packet["window_metrics"] == {
        "window": "fixed_eight_A_cases",
        "requests": 8,
        "technical_successes": 3,
        "technical_success_denominator": 8,
        "technical_errors": 2,
        "technical_error_denominator": 8,
        "cancellations": 1,
        "refusals": 1,
        "permission_denials": 1,
        "simulated_request_latencies_ms_sorted": [10, 10, 10, 10, 20, 20, 20, 30],
        "simulated_p95_ms_nearest_rank": 30,
        "authored_proposal_events": 7,
        "real_model_calls": 0,
        "tool_attempt_events": 5,
        "simulated_cost_credits": 10,
        "simulated_budget_credits": 16,
        "simulated_remaining_credits": 6,
        "live_quality_labels_received": 0,
        "live_quality_denominator": 0,
        "live_quality_rate": None,
    }
    assert packet["a_disclaimer"] == agents.build_demo()["disclaimer"]
    serialized = json.dumps(packet, ensure_ascii=False)
    assert "approval_target" not in serialized
    assert "checkpoint" not in serialized
    assert "pickup_at" not in serialized
    assert "Ночное хранение" not in serialized


def test_manifest_hashes_actual_a_source_and_guide() -> None:
    manifest = production.build_packet()["manifest"]
    assert agents.__file__ is not None
    source = Path(agents.__file__)
    assert manifest["workflow_source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert production.__file__ is not None
    assert (
        manifest["operations_source_sha256"]
        == hashlib.sha256(Path(production.__file__).read_bytes()).hexdigest()
    )
    rollback = importlib.import_module("modules.08_production_ai.06_rollout_incidents.example")
    assert rollback.__file__ is not None
    assert (
        manifest["rollback_source_sha256"]
        == hashlib.sha256(Path(rollback.__file__).read_bytes()).hexdigest()
    )
    assert manifest["guide_fixture_sha256"] == hashlib.sha256(agents.GUIDE.encode()).hexdigest()
    protocol_bytes = json.dumps(
        production.EVALUATION_PROTOCOL,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert manifest["evaluation_protocol_sha256"] == hashlib.sha256(protocol_bytes).hexdigest()
    repo = Path(__file__).resolve().parents[2]
    assert (
        manifest["dependency_lock_sha256"]
        == hashlib.sha256((repo / "uv.lock").read_bytes()).hexdigest()
    )
    assert (
        manifest["project_config_sha256"]
        == hashlib.sha256((repo / "pyproject.toml").read_bytes()).hexdigest()
    )
    assert manifest["runtime"]["python_implementation"] == platform.python_implementation()
    assert manifest["runtime"]["python_version"] == platform.python_version()
    for name in ("fastapi", "starlette", "pydantic", "anyio"):
        assert manifest["runtime"]["installed_dependency_versions"][name] == (
            importlib.metadata.version(name)
        )
    cases = agents.build_demo()["cases"]
    selected = {name: cases[name] for name in production.WINDOW_CASES}
    selected_bytes = json.dumps(
        selected, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    assert manifest["selected_input_fixture_sha256"] == hashlib.sha256(selected_bytes).hexdigest()
    contract = {
        "case_fields": sorted(cases["answer"]),
        "trace_event_fields": sorted(cases["answer"]["trace"][0]),
        "window_case_ids": list(production.WINDOW_CASES),
    }
    contract_bytes = json.dumps(
        contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    assert manifest["input_contract_sha256"] == hashlib.sha256(contract_bytes).hexdigest()
    decisions = production.build_packet()["candidate_decisions"]
    fixture = {
        "baseline_fixture_labels": decisions["baseline_fixture_labels"],
        "candidate_evidence": decisions["candidate_evidence"],
    }
    fixture_bytes = json.dumps(
        fixture, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    assert (
        manifest["authored_evaluation_fixture_sha256"] == hashlib.sha256(fixture_bytes).hexdigest()
    )
    assert manifest["model_artifact"] is None
    assert manifest["retrieval_index"] is None


def test_manifest_identity_changes_with_isolated_fixture_edits() -> None:
    original_cases = agents.build_demo()["cases"]
    original_decisions = production.build_packet()["candidate_decisions"]
    original = production._release_manifest(agents, original_cases, original_decisions)
    edited_cases = deepcopy(original_cases)
    edited_cases["answer"]["elapsed_ms"] = 11
    changed_input = production._release_manifest(agents, edited_cases, original_decisions)
    assert (
        changed_input["selected_input_fixture_sha256"] != original["selected_input_fixture_sha256"]
    )
    assert (
        changed_input["authored_evaluation_fixture_sha256"]
        == original["authored_evaluation_fixture_sha256"]
    )
    edited_decisions = deepcopy(original_decisions)
    edited_decisions["candidate_evidence"]["faster_critical_regression"]["labels"]["answer"] = True
    changed_candidate = production._release_manifest(agents, original_cases, edited_decisions)
    assert (
        changed_candidate["authored_evaluation_fixture_sha256"]
        != original["authored_evaluation_fixture_sha256"]
    )
    assert (
        changed_candidate["selected_input_fixture_sha256"]
        == original["selected_input_fixture_sha256"]
    )


def test_incident_facts_follow_a_case_without_remote_claim() -> None:
    original = agents.build_demo()["cases"]["unknown_after_effect"]
    incident = production.build_packet()["incident"]
    assert incident["facts"] == {
        "run_id": "unknown_after_effect",
        "outcome": "unknown_needs_reconciliation",
        "tool_attempt_events": 1,
        "last_tool_result": "response_lost",
        "attempts": 1,
        "effects_in_privileged_simulator": 1,
        "receipt": None,
    }
    assert incident["remote_reconciliation"] == "NOT_VERIFIED"
    edited = deepcopy(original)
    edited["attempts"] = 2
    edited["trace"][-1]["result"] = "different_local_result"
    changed = production._incident_from_case(edited)
    assert changed["facts"]["attempts"] == 2
    assert changed["facts"]["last_tool_result"] == "different_local_result"
    assert "attempts=2" in changed["timeline"][-1]
    assert "different_local_result" in changed["timeline"][3]


def test_decisions_are_frozen_paired_local_evidence() -> None:
    decisions = production.build_packet()["candidate_decisions"]
    assert decisions["protocol"]["heldout_case_ids"] == [
        "answer",
        "denied",
        "refused",
        "success",
    ]
    assert decisions["protocol"]["critical_case_ids"] == ["answer"]
    assert decisions["results"] == {
        "faster_critical_regression": "reject",
        "missing_required_label": "hold_insufficient_evidence",
        "compatible_complete_fixture": "locally_eligible",
        "incompatible_rollback": "block_incompatible",
    }
    assert decisions["candidate_evidence"]["faster_critical_regression"]["simulated_p95_ms"] < 30
    assert decisions["candidate_evidence"]["missing_required_label"]["labels"]["answer"] is None


def test_existing_directory_is_refused_without_clobber(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("untouched", encoding="utf-8")
    with pytest.raises(FileExistsError):
        production.save_packet(target)
    assert sentinel.read_text(encoding="utf-8") == "untouched"
    assert list(target.iterdir()) == [sentinel]
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileExistsError):
        production.save_packet(empty)


def test_fresh_outputs_reproducible_and_contain_only_teacher_artifacts(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    production.save_packet(first)
    production.save_packet(second)
    expected = {
        "observed_events.json",
        "manifest.json",
        "window_metrics.json",
        "candidate_decisions.json",
        "incident.json",
    }
    assert {path.name for path in first.iterdir()} == expected
    assert {path.name for path in second.iterdir()} == expected
    for name in expected:
        assert (first / name).read_bytes() == (second / name).read_bytes()
        json.loads((first / name).read_text(encoding="utf-8"))
