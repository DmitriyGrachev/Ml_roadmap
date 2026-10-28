"""Offline operations view of the fixed Module 07 bicycle-service walkthrough.

All proposals, candidate labels, latency, and credits are authored fixtures. No
model, provider, deployment, or external reminder is invoked.
"""

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
from importlib import import_module
from pathlib import Path
from typing import Any

WINDOW_CASES = (
    "answer",
    "success",
    "denied",
    "refused",
    "cancelled",
    "failure_recovered",
    "attempt_exhausted",
    "unknown_after_effect",
)
RELEASE_ID = "G01-scripted-workflow-v1"
EVALUATION_PROTOCOL: dict[str, Any] = {
    "heldout_case_ids": ["answer", "denied", "refused", "success"],
    "critical_case_ids": ["answer"],
    "required_labels": "all four paired fixture cases",
    "maximum_critical_regressions": 0,
    "maximum_other_regressions": 0,
    "maximum_simulated_p95_ms": 30,
    "rollback_requires_compatible_schema_and_available_artifact": True,
}


def _encoded(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _observed_events(cases: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for name in WINDOW_CASES:
        case = cases[name]
        trace = case["trace"]
        events.append(
            {
                "run_id": case["run_id"],
                "release_id": RELEASE_ID,
                "outcome": case["outcome"],
                "steps": case["steps"],
                "attempts": case["attempts"],
                "simulated_request_latency_ms": case["elapsed_ms"],
                "authored_proposal_events": sum(row["event"] == "proposal" for row in trace),
                "real_model_calls": 0,
                "tool_attempt_events": sum(row["event"] == "tool_attempt" for row in trace),
                "reference_label": None,
            }
        )
    return events


def _window_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = sorted(row["simulated_request_latency_ms"] for row in events)
    attempts = sum(row["tool_attempt_events"] for row in events)
    label_count = sum(row["reference_label"] is not None for row in events)
    return {
        "window": "fixed_eight_A_cases",
        "requests": len(events),
        "technical_successes": sum(
            row["outcome"] in {"answered", "reminder_recorded"} for row in events
        ),
        "technical_success_denominator": len(events),
        "technical_errors": sum(
            row["outcome"] in {"attempt_limit", "unknown_needs_reconciliation"} for row in events
        ),
        "technical_error_denominator": len(events),
        "cancellations": sum(row["outcome"] == "cancel" for row in events),
        "refusals": sum(row["outcome"] == "refuse" for row in events),
        "permission_denials": sum(row["outcome"] == "permission_denied" for row in events),
        "simulated_request_latencies_ms_sorted": latencies,
        "simulated_p95_ms_nearest_rank": latencies[math.ceil(0.95 * len(latencies)) - 1],
        "authored_proposal_events": sum(row["authored_proposal_events"] for row in events),
        "real_model_calls": sum(row["real_model_calls"] for row in events),
        "tool_attempt_events": attempts,
        "simulated_cost_credits": attempts * 2,
        "simulated_budget_credits": 16,
        "simulated_remaining_credits": 16 - attempts * 2,
        "live_quality_labels_received": label_count,
        "live_quality_denominator": label_count,
        "live_quality_rate": None,
    }


def _candidate_decisions() -> dict[str, Any]:
    """Apply this packet's fixed, tiny rubric to explicitly authored candidate rows."""
    release = import_module("modules.08_production_ai.06_rollout_incidents.example")
    baseline_labels = dict.fromkeys(EVALUATION_PROTOCOL["heldout_case_ids"], True)
    candidates: dict[str, dict[str, Any]] = {
        "faster_critical_regression": {
            "labels": {"answer": False, "denied": True, "refused": True, "success": True},
            "simulated_p95_ms": 20,
            "stored_schema": 1,
            "artifact_available": True,
        },
        "missing_required_label": {
            "labels": {"answer": None, "denied": True, "refused": True, "success": True},
            "simulated_p95_ms": 20,
            "stored_schema": 1,
            "artifact_available": True,
        },
        "compatible_complete_fixture": {
            "labels": {"answer": True, "denied": True, "refused": True, "success": True},
            "simulated_p95_ms": 20,
            "stored_schema": 1,
            "artifact_available": True,
        },
        "incompatible_rollback": {
            "labels": {"answer": True, "denied": True, "refused": True, "success": True},
            "simulated_p95_ms": 20,
            "stored_schema": 2,
            "artifact_available": True,
        },
    }
    previous = release.Release("G01-scripted-workflow-v1", frozenset({1}))
    results: dict[str, str] = {}
    for name, row in candidates.items():
        labels = row["labels"]
        if not release.rollback_preflight(
            previous, row["stored_schema"], row["artifact_available"]
        ):
            result = "block_incompatible"
        elif set(labels) != set(baseline_labels) or any(value is None for value in labels.values()):
            result = "hold_insufficient_evidence"
        elif (
            any(baseline_labels[case_id] and not labels[case_id] for case_id in labels)
            or row["simulated_p95_ms"] > EVALUATION_PROTOCOL["maximum_simulated_p95_ms"]
        ):
            result = "reject"
        else:
            result = "locally_eligible"
        results[name] = result
    return {
        "protocol": EVALUATION_PROTOCOL,
        "baseline_fixture_labels": baseline_labels,
        "candidate_evidence": candidates,
        "results": results,
        "limit": (
            "Authored paired fixture labels; local eligibility is not production certification."
        ),
    }


def _release_manifest(
    agents: Any, cases: dict[str, Any], decisions: dict[str, Any]
) -> dict[str, Any]:
    """Identify this scripted code, exact fixture data, and installed runtime."""
    if agents.__file__ is None:
        raise RuntimeError("Module 07 source file is required for the manifest")
    rollback = import_module("modules.08_production_ai.06_rollout_incidents.example")
    if rollback.__file__ is None:
        raise RuntimeError("Rollback example source file is required for the manifest")
    repo = Path(__file__).resolve().parents[2]
    selected = {name: cases[name] for name in WINDOW_CASES}
    input_contract = {
        "case_fields": sorted(cases["answer"]),
        "trace_event_fields": sorted(cases["answer"]["trace"][0]),
        "window_case_ids": list(WINDOW_CASES),
    }
    authored_fixture = {
        "baseline_fixture_labels": decisions["baseline_fixture_labels"],
        "candidate_evidence": decisions["candidate_evidence"],
    }
    return {
        "release_id": RELEASE_ID,
        "workflow_source": "modules/07_agents/walkthrough.py",
        "workflow_source_sha256": hashlib.sha256(Path(agents.__file__).read_bytes()).hexdigest(),
        "operations_source": "modules/08_production_ai/walkthrough.py",
        "operations_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rollback_source": "modules/08_production_ai/06_rollout_incidents/example.py",
        "rollback_source_sha256": hashlib.sha256(Path(rollback.__file__).read_bytes()).hexdigest(),
        "guide_fixture_id": "G-01@2026-09:p1",
        "guide_fixture_sha256": hashlib.sha256(agents.GUIDE.encode("utf-8")).hexdigest(),
        "input_contract_sha256": hashlib.sha256(_encoded(input_contract)).hexdigest(),
        "selected_input_fixture_sha256": hashlib.sha256(_encoded(selected)).hexdigest(),
        "evaluation_protocol_sha256": hashlib.sha256(_encoded(EVALUATION_PROTOCOL)).hexdigest(),
        "authored_evaluation_fixture_sha256": hashlib.sha256(
            _encoded(authored_fixture)
        ).hexdigest(),
        "project_config_sha256": hashlib.sha256((repo / "pyproject.toml").read_bytes()).hexdigest(),
        "dependency_lock_sha256": hashlib.sha256((repo / "uv.lock").read_bytes()).hexdigest(),
        "runtime": {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "installed_dependency_versions": {
                name: importlib.metadata.version(name)
                for name in ("fastapi", "starlette", "pydantic", "anyio")
            },
        },
        "model_artifact": None,
        "preprocessing_artifact": None,
        "retrieval_index": None,
        "prompt_artifact": None,
        "input_contract": "Part A fixed request and exact-action fixture",
        "label_contract": "Four authored paired reference outcomes, no live quality labels",
    }


def _incident_from_case(case: dict[str, Any]) -> dict[str, Any]:
    """Summarize checkable A facts without claiming remote reconciliation."""
    tool_events = [row for row in case["trace"] if row["event"] == "tool_attempt"]
    last_result = tool_events[-1]["result"] if tool_events else None
    facts = {
        "run_id": case["run_id"],
        "outcome": case["outcome"],
        "tool_attempt_events": len(tool_events),
        "last_tool_result": last_result,
        "attempts": case["attempts"],
        "effects_in_privileged_simulator": case["effects"],
        "receipt": case["receipt"],
    }
    if last_result == "response_lost" and case["effects"] == 1:
        local_check = "rules out pre-effect failure in this fixture"
    else:
        local_check = "does not establish whether the local effect occurred"
    return {
        "scenario": "G-01 simulated response lost after local effect",
        "facts": facts,
        "remote_reconciliation": "NOT_VERIFIED",
        "timeline": [
            f"T0 symptom: {case['run_id']} ended {case['outcome']}.",
            f"T1 signals: {len(tool_events)} tool_attempt event(s), effects={case['effects']} "
            f"in privileged A simulator; receipt={case['receipt']}.",
            "T2 hypotheses: failure before effect or effect then lost reply.",
            f"T3 local check: trace result={last_result} plus effects={case['effects']} "
            f"{local_check}; no remote receipt was checked.",
            "T4 containment chosen: no automatic retry; mark this run held for "
            "authoritative reconciliation by the operation owner.",
            "T5 local recovery decision: do not re-execute; previous bundle reads schema 1 "
            "and its source artifact is available. Remote recovery remains unverified.",
            f"T6 local post-check: this run still has attempts={case['attempts']}, "
            f"effects={case['effects']} and receipt={case['receipt']}; "
            "live quality labels remain absent.",
        ],
        "limit": (
            "A's local effects counter is privileged fixture knowledge, "
            "not evidence of remote delivery."
        ),
    }


def build_packet() -> dict[str, Any]:
    """Read Part A's stable API and derive a deterministic, bounded teacher packet."""
    agents = import_module("modules.07_agents.walkthrough")
    demo = agents.build_demo()
    events = _observed_events(demo["cases"])
    decisions = _candidate_decisions()
    manifest = _release_manifest(agents, demo["cases"], decisions)
    incident = _incident_from_case(demo["cases"]["unknown_after_effect"])
    return {
        "a_disclaimer": demo["disclaimer"],
        "observed_events": events,
        "manifest": manifest,
        "window_metrics": _window_metrics(events),
        "candidate_decisions": decisions,
        "incident": incident,
    }


def save_packet(output_dir: Path) -> Path:
    """Create only a fresh output directory; existing empty directories also fail."""
    output_dir.mkdir(parents=True, exist_ok=False)
    packet = build_packet()
    for key in (
        "observed_events",
        "manifest",
        "window_metrics",
        "candidate_decisions",
        "incident",
    ):
        (output_dir / f"{key}.json").write_text(
            json.dumps(packet[key], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output = save_packet(args.output_dir)
    metrics = json.loads((output / "window_metrics.json").read_text(encoding="utf-8"))
    print(f"Teacher packet: {output}")
    print(
        f"Fixed window: {metrics['requests']} requests, "
        f"{metrics['tool_attempt_events']} simulated tool attempts, "
        f"{metrics['real_model_calls']} real model calls, "
        f"{metrics['live_quality_labels_received']} live quality labels."
    )


if __name__ == "__main__":
    main()
