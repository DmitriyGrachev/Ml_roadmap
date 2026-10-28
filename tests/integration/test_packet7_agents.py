"""Behavioral checks for the offline pickup-reminder teacher walkthrough."""

import importlib
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

demo = importlib.import_module("modules.07_agents.walkthrough")
DEFAULT_POLICY = demo.RunPolicy(3, 2, 100)


def test_plain_answer_uses_fixed_public_guide_without_effect() -> None:
    result = demo.answer_only("run-answer")
    assert result["outcome"] == "answered"
    assert result["answer"] == "Ночное хранение не предлагается. Заберите велосипед до 19:00."
    assert result["effects"] == 0
    assert result["source"] == "G-01@2026-09:p1"


def test_approval_is_exact_and_rechecked_at_effect_boundary() -> None:
    pending = demo.propose_reminder("run-1", "call-1", "19:00", can_remind=True)
    assert pending["outcome"] == "awaiting_confirmation"
    assert pending["effects"] == 0
    approved = demo.resolve_reminder(
        pending["checkpoint"],
        "approve",
        pending["approval_target"],
        policy=DEFAULT_POLICY,
        can_remind=True,
    )
    assert approved["outcome"] == "reminder_recorded"
    assert approved["effects"] == 1
    assert approved["receipt"] == "call-1"
    replay = demo.resolve_reminder(
        approved["checkpoint"],
        "approve",
        pending["approval_target"],
        policy=DEFAULT_POLICY,
        can_remind=True,
    )
    assert replay["effects"] == 1
    assert replay["trace"] == approved["trace"]


@pytest.mark.parametrize("decision", ["refuse", "cancel"])
def test_refusal_and_cancellation_have_zero_effect(decision: str) -> None:
    pending = demo.propose_reminder("run-2", "call-2", "19:00", can_remind=True)
    result = demo.resolve_reminder(
        pending["checkpoint"], decision, policy=DEFAULT_POLICY, can_remind=True
    )
    assert result["outcome"] == decision
    assert result["effects"] == 0
    assert result["attempts"] == 0


def test_denied_or_invalid_proposal_never_performs_action() -> None:
    denied = demo.propose_reminder("run-3", "call-3", "19:00", can_remind=False)
    invalid = demo.propose_reminder("run-4", "call-4", "20:00", can_remind=True)
    assert denied["outcome"] == "permission_denied"
    assert denied["effects"] == 0
    assert invalid["outcome"] == "invalid_proposal"
    assert invalid["effects"] == 0


def test_changed_arguments_need_new_approval() -> None:
    pending = demo.propose_reminder("run-5", "call-5", "19:00", can_remind=True)
    result = demo.resolve_reminder(
        pending["checkpoint"],
        "approve",
        pending["approval_target"],
        pickup_at="18:00",
        policy=DEFAULT_POLICY,
        can_remind=True,
    )
    assert result["outcome"] == "approval_mismatch"
    assert result["effects"] == 0
    assert result["attempts"] == 0


def test_failure_before_effect_retries_within_attempt_budget() -> None:
    pending = demo.propose_reminder("run-6", "call-6", "19:00", can_remind=True)
    failed = demo.resolve_reminder(
        pending["checkpoint"],
        "approve",
        pending["approval_target"],
        result="before_effect_error",
        policy=DEFAULT_POLICY,
        can_remind=True,
    )
    assert failed["outcome"] == "retryable_failure"
    assert failed["attempts"] == 1
    assert failed["effects"] == 0
    recovered = demo.resolve_reminder(
        failed["checkpoint"],
        "approve",
        pending["approval_target"],
        policy=DEFAULT_POLICY,
        can_remind=True,
    )
    assert recovered["outcome"] == "reminder_recorded"
    assert recovered["attempts"] == 2
    assert recovered["effects"] == 1


@pytest.mark.parametrize(
    ("limit", "reason"),
    [
        ({"max_attempts": 1}, "attempt_limit"),
        ({"max_steps": 1}, "step_limit"),
        ({"deadline_ms": 10}, "time_limit"),
    ],
)
def test_attempt_step_and_time_limits_prevent_later_calls(
    limit: dict[str, int], reason: str
) -> None:
    policy = demo.RunPolicy(
        limit.get("max_steps", 3), limit.get("max_attempts", 2), limit.get("deadline_ms", 100)
    )
    pending = demo.propose_reminder("run-limit", "call-7", "19:00", can_remind=True, **limit)
    first = demo.resolve_reminder(
        pending["checkpoint"],
        "approve",
        pending["approval_target"],
        result="before_effect_error",
        policy=policy,
        can_remind=True,
    )
    second = demo.resolve_reminder(
        first["checkpoint"],
        "approve",
        pending["approval_target"],
        policy=policy,
        can_remind=True,
    )
    assert second["effects"] == 0
    assert second["attempts"] <= 1
    assert second["outcome"] == reason


@pytest.mark.parametrize(
    ("field", "limits", "raised"),
    [
        ("max_attempts", {"max_steps": 4, "max_attempts": 1, "deadline_ms": 100}, 2),
        ("max_steps", {"max_steps": 2, "max_attempts": 3, "deadline_ms": 100}, 3),
        ("deadline_ms", {"max_steps": 4, "max_attempts": 3, "deadline_ms": 20}, 30),
    ],
)
def test_saved_limits_cannot_be_raised_to_retry_after_exhaustion(
    field: str, limits: dict[str, int], raised: int
) -> None:
    pending = demo.propose_reminder("run-policy", "call-11", "19:00", can_remind=True, **limits)
    failed = demo.resolve_reminder(
        pending["checkpoint"],
        "approve",
        pending["approval_target"],
        result="before_effect_error",
        policy=demo.RunPolicy(**limits),
        can_remind=True,
    )
    saved = json.loads(failed["checkpoint"])
    saved[field] = raised
    with pytest.raises(ValueError, match="policy"):
        demo.resolve_reminder(
            json.dumps(saved),
            "approve",
            pending["approval_target"],
            policy=demo.RunPolicy(**limits),
            can_remind=True,
        )


def test_unknown_after_effect_blocks_blind_retry() -> None:
    pending = demo.propose_reminder("run-8", "call-8", "19:00", can_remind=True)
    unknown = demo.resolve_reminder(
        pending["checkpoint"],
        "approve",
        pending["approval_target"],
        result="response_lost",
        policy=DEFAULT_POLICY,
        can_remind=True,
    )
    again = demo.resolve_reminder(
        unknown["checkpoint"],
        "approve",
        pending["approval_target"],
        policy=DEFAULT_POLICY,
        can_remind=True,
    )
    assert unknown["outcome"] == again["outcome"] == "unknown_needs_reconciliation"
    assert again["effects"] == 1
    assert again["attempts"] == 1


def test_checkpoint_roundtrip_resumes_saved_state_and_rejects_tampering() -> None:
    pending = demo.propose_reminder("run-9", "call-9", "19:00", can_remind=True)
    saved = json.loads(pending["checkpoint"])
    resumed = demo.resolve_reminder(
        json.dumps(saved),
        "approve",
        pending["approval_target"],
        policy=DEFAULT_POLICY,
        can_remind=True,
    )
    assert resumed["run_id"] == "run-9"
    assert resumed["receipt"] == "call-9"
    saved["effects"] = 1
    with pytest.raises(ValueError, match="effect without receipt"):
        demo.resolve_reminder(
            json.dumps(saved),
            "approve",
            pending["approval_target"],
            policy=DEFAULT_POLICY,
            can_remind=True,
        )
    saved["schema_version"] = 999
    with pytest.raises(ValueError, match="version"):
        demo.resolve_reminder(
            json.dumps(saved),
            "approve",
            pending["approval_target"],
            policy=DEFAULT_POLICY,
            can_remind=True,
        )


def test_permission_is_rechecked_on_resume_and_trace_cannot_claim_fresh_status() -> None:
    pending = demo.propose_reminder("run-10", "call-10", "19:00", can_remind=True)
    revoked = demo.resolve_reminder(
        pending["checkpoint"],
        "approve",
        pending["approval_target"],
        policy=DEFAULT_POLICY,
        can_remind=False,
    )
    assert revoked["outcome"] == "permission_denied"
    assert revoked["effects"] == 0
    saved = json.loads(pending["checkpoint"])
    saved["status"] = "retryable_failure"
    with pytest.raises(ValueError, match="trace"):
        demo.resolve_reminder(
            json.dumps(saved),
            "approve",
            pending["approval_target"],
            policy=DEFAULT_POLICY,
            can_remind=True,
        )


def test_cli_refuses_even_existing_empty_output_and_uses_no_network(tmp_path: Path) -> None:
    original = socket.socket.connect

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network attempted")

    socket.socket.connect = blocked
    try:
        importlib.reload(demo)
        fresh = tmp_path / "fresh"
        trace = demo.save_demo(fresh)
        assert trace.exists()
        assert (fresh / "checkpoint.json").exists()
        with pytest.raises(FileExistsError):
            demo.save_demo(fresh)
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(FileExistsError):
            demo.save_demo(empty)
    finally:
        socket.socket.connect = original
    cli = subprocess.run(
        [sys.executable, "-m", "modules.07_agents.walkthrough", "--output", str(tmp_path / "cli")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cli.returncode == 0, cli.stderr
