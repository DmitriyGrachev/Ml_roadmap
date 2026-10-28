"""Offline teacher walkthrough for the fixed G-01 pickup rule.

Proposals and answers are authored fixtures. The only effect is a counter in a
serialized, trusted-origin teaching checkpoint; no reminder is delivered.
"""

import argparse
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, cast

approval_digest = cast(
    Callable[[str, int, str, dict[str, str]], str],
    import_module("modules.07_agents.04_checkpoints_approvals.example").approval_digest,
)
stop_reason = cast(
    Callable[[int, int, int, int], str | None],
    import_module("modules.07_agents.03_bounded_agents.example").stop_reason,
)

GUIDE = "Overnight storage is not offered. Pickup by 19:00."
ANSWER = "Ночное хранение не предлагается. Заберите велосипед до 19:00."
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RunPolicy:
    """Limits supplied by the application again at resume, outside the checkpoint."""

    max_steps: int
    max_attempts: int
    deadline_ms: int

    def __post_init__(self) -> None:
        for value in (self.max_steps, self.max_attempts, self.deadline_ms):
            if type(value) is not int or value < 1:
                raise ValueError("policy limits must be positive integers")


FIELDS = {
    "schema_version",
    "run_id",
    "version",
    "call_id",
    "pickup_at",
    "approval_target",
    "status",
    "steps",
    "attempts",
    "effects",
    "receipt",
    "max_steps",
    "max_attempts",
    "deadline_ms",
    "elapsed_ms",
    "trace",
}
TERMINAL = {
    "answered",
    "permission_denied",
    "invalid_proposal",
    "reminder_recorded",
    "refuse",
    "cancel",
    "approval_mismatch",
    "attempt_limit",
    "step_limit",
    "time_limit",
    "unknown_needs_reconciliation",
}


def _event(
    state: dict[str, Any],
    event: str,
    check: str,
    action: str,
    after: str,
    *,
    result: str = "none",
) -> None:
    state["trace"].append(
        {
            "step": state["steps"],
            "attempt": state["attempts"],
            "before": state["status"],
            "event": event,
            "check": check,
            "action": action,
            "after": after,
            "tool": "simulate_pickup_reminder" if state["call_id"] else None,
            "arguments": {"pickup_at": state["pickup_at"]} if state["pickup_at"] else {},
            "result": result,
        }
    )
    state["status"] = after


def _target(state: dict[str, Any]) -> str:
    return approval_digest(
        state["run_id"],
        state["version"],
        "simulate_pickup_reminder",
        {"call_id": state["call_id"], "pickup_at": state["pickup_at"]},
    )


def _view(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": state["run_id"],
        "outcome": state["status"],
        "answer": ANSWER,
        "source": "G-01@2026-09:p1",
        "approval_target": state["approval_target"],
        "steps": state["steps"],
        "attempts": state["attempts"],
        "elapsed_ms": state["elapsed_ms"],
        "effects": state["effects"],
        "receipt": state["receipt"],
        "trace": state["trace"],
        "checkpoint": json.dumps(state, ensure_ascii=False, sort_keys=True),
    }


def _initial(
    run_id: str,
    call_id: str | None,
    pickup_at: str | None,
    max_steps: int,
    max_attempts: int,
    deadline_ms: int,
) -> dict[str, Any]:
    if not run_id or not isinstance(run_id, str):
        raise ValueError("run_id required")
    for value, name in (
        (max_steps, "max_steps"),
        (max_attempts, "max_attempts"),
        (deadline_ms, "deadline_ms"),
    ):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be positive integer")
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "version": 1,
        "call_id": call_id,
        "pickup_at": pickup_at,
        "approval_target": None,
        "status": "new",
        "steps": 0,
        "attempts": 0,
        "effects": 0,
        "receipt": None,
        "max_steps": max_steps,
        "max_attempts": max_attempts,
        "deadline_ms": deadline_ms,
        "elapsed_ms": 0,
        "trace": [],
    }


def answer_only(run_id: str) -> dict[str, Any]:
    """Plain deterministic function sequence: read fixed public fixture, answer."""
    state = _initial(run_id, None, None, 2, 2, 100)
    state["steps"] = 1
    state["elapsed_ms"] = 10
    _event(state, "read_G-01", "public_fixture", "prepare_canned_answer", "answered", result=GUIDE)
    return _view(state)


def propose_reminder(
    run_id: str,
    call_id: str,
    pickup_at: str,
    *,
    can_remind: bool,
    max_steps: int = 3,
    max_attempts: int = 2,
    deadline_ms: int = 100,
) -> dict[str, Any]:
    """Scripted model proposal, checked before requesting human confirmation."""
    state = _initial(run_id, call_id, pickup_at, max_steps, max_attempts, deadline_ms)
    state["steps"] = 1
    state["elapsed_ms"] = 10
    if (
        not isinstance(call_id, str)
        or not re.fullmatch(r"call-[0-9]+", call_id)
        or not isinstance(pickup_at, str)
        or not re.fullmatch(r"[0-2][0-9]:[0-5][0-9]", pickup_at)
    ):
        _event(state, "proposal", "schema_invalid", "no_action", "invalid_proposal")
    elif pickup_at > "19:00":
        _event(state, "proposal", "operation_limit", "no_action", "invalid_proposal")
    elif can_remind is not True:
        _event(state, "proposal", "permission_denied", "no_action", "permission_denied")
    else:
        state["approval_target"] = _target(state)
        _event(
            state,
            "proposal",
            "schema_values_permission_limits_ok",
            "request_exact_confirmation",
            "awaiting_confirmation",
        )
    return _view(state)


def _restore(checkpoint: str, policy: RunPolicy) -> dict[str, Any]:
    """Validate JSON against application-owned limits before any action."""
    if not isinstance(policy, RunPolicy):
        raise ValueError("application policy required")
    try:
        state = json.loads(checkpoint)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("invalid checkpoint JSON") from error
    if not isinstance(state, dict) or set(state) != FIELDS:
        raise ValueError("invalid checkpoint fields")
    if type(state["schema_version"]) is not int or state["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported checkpoint version")
    if type(state["version"]) is not int or state["version"] != 1:
        raise ValueError("invalid workflow version")
    if not isinstance(state["run_id"], str) or not state["run_id"]:
        raise ValueError("invalid run ID")
    for key in (
        "steps",
        "attempts",
        "effects",
        "elapsed_ms",
        "max_steps",
        "max_attempts",
        "deadline_ms",
    ):
        if type(state[key]) is not int or state[key] < 0:
            raise ValueError(f"invalid {key}")
    if min(state["max_steps"], state["max_attempts"], state["deadline_ms"]) < 1:
        raise ValueError("invalid limits")
    if (
        state["max_steps"] != policy.max_steps
        or state["max_attempts"] != policy.max_attempts
        or state["deadline_ms"] != policy.deadline_ms
    ):
        raise ValueError("checkpoint limits differ from application policy")
    if state["steps"] > state["max_steps"] or state["attempts"] > state["max_attempts"]:
        raise ValueError("counter exceeded")
    if not isinstance(state["trace"], list) or len(state["trace"]) == 0:
        raise ValueError("invalid trace")
    last = state["trace"][-1]
    if (
        not isinstance(last, dict)
        or last.get("after") != state["status"]
        or last.get("step") != state["steps"]
        or last.get("attempt") != state["attempts"]
    ):
        raise ValueError("checkpoint trace mismatch")
    if state["status"] not in TERMINAL | {"awaiting_confirmation", "retryable_failure"}:
        raise ValueError("invalid state")
    if state["status"] in {
        "awaiting_confirmation",
        "retryable_failure",
        "reminder_recorded",
        "unknown_needs_reconciliation",
    }:
        if not isinstance(state["call_id"], str) or not re.fullmatch(
            r"call-[0-9]+", state["call_id"]
        ):
            raise ValueError("invalid call")
        if (
            not isinstance(state["pickup_at"], str)
            or not re.fullmatch(r"[0-2][0-9]:[0-5][0-9]", state["pickup_at"])
            or state["pickup_at"] > "19:00"
        ):
            raise ValueError("invalid pickup time")
        if state["approval_target"] != _target(state):
            raise ValueError("invalid approval target")
    if state["status"] == "reminder_recorded":
        if state["receipt"] != state["call_id"] or state["effects"] != 1 or state["attempts"] < 1:
            raise ValueError("invalid receipt")
    elif state["status"] == "unknown_needs_reconciliation":
        if state["receipt"] is not None or state["effects"] != 1 or state["attempts"] < 1:
            raise ValueError("invalid unknown outcome")
    elif state["effects"] != 0 or state["receipt"] is not None:
        raise ValueError("effect without receipt")
    return state


def resolve_reminder(
    checkpoint: str,
    decision: str,
    approval: str | None = None,
    *,
    pickup_at: str | None = None,
    result: str = "success",
    policy: RunPolicy,
    can_remind: bool,
) -> dict[str, Any]:
    """Resume only saved state; the operation remains a local counter increment."""
    state = _restore(checkpoint, policy)
    if state["status"] in TERMINAL:
        return _view(state)
    if decision in {"refuse", "cancel"}:
        _event(state, decision, "human_decision", "no_action", decision)
        return _view(state)
    if decision != "approve":
        raise ValueError("unknown human decision")
    if (pickup_at is not None and pickup_at != state["pickup_at"]) or (
        approval != state["approval_target"]
    ):
        _event(state, "approve", "approval_mismatch", "no_action", "approval_mismatch")
        return _view(state)
    if can_remind is not True:
        _event(state, "approve", "permission_denied", "no_action", "permission_denied")
        return _view(state)
    if state["attempts"] >= state["max_attempts"]:
        _event(state, "retry", "attempt_limit", "no_action", "attempt_limit")
        return _view(state)
    boundary = stop_reason(
        state["steps"], state["max_steps"], state["elapsed_ms"], state["deadline_ms"]
    )
    if boundary is not None:
        reason = "time_limit" if boundary == "deadline" else "step_limit"
        _event(state, "retry", reason, "no_action", reason)
        return _view(state)
    if result not in {"success", "before_effect_error", "response_lost"}:
        raise ValueError("unknown simulated result")
    state["steps"] += 1
    state["attempts"] += 1
    state["elapsed_ms"] += 10
    if result == "before_effect_error":
        _event(
            state,
            "tool_attempt",
            "permission_rechecked",
            "simulate_failure_before_effect",
            "retryable_failure",
            result=result,
        )
    elif result == "response_lost":
        state["effects"] += 1
        _event(
            state,
            "tool_attempt",
            "permission_rechecked",
            "simulate_effect_then_lose_response",
            "unknown_needs_reconciliation",
            result=result,
        )
    else:
        state["effects"] += 1
        state["receipt"] = state["call_id"]
        _event(
            state,
            "tool_attempt",
            "permission_rechecked",
            "simulate_local_reminder_record",
            "reminder_recorded",
            result="receipt_recorded",
        )
    return _view(state)


def build_demo() -> dict[str, Any]:
    """Finite authored cases; no model loop, scheduler, or external action."""
    cases: dict[str, Any] = {"answer": answer_only("answer")}
    scenarios: dict[str, dict[str, Any]] = {
        "success": {},
        "denied": {"can_remind": False},
        "invalid": {"pickup_at": "20:00"},
        "waiting": {},
        "refused": {},
        "cancelled": {},
        "changed_args": {},
        "failure_recovered": {},
        "attempt_exhausted": {"max_attempts": 1},
        "known_replay": {},
        "unknown_after_effect": {},
        "step_limit": {"max_steps": 1},
        "time_limit": {"deadline_ms": 10},
    }
    for case, options in scenarios.items():
        policy = RunPolicy(
            max_steps=options.get("max_steps", 3),
            max_attempts=options.get("max_attempts", 2),
            deadline_ms=options.get("deadline_ms", 100),
        )
        pending = propose_reminder(
            case,
            "call-1",
            options.get("pickup_at", "19:00"),
            can_remind=options.get("can_remind", True),
            max_steps=policy.max_steps,
            max_attempts=policy.max_attempts,
            deadline_ms=policy.deadline_ms,
        )
        if case in {"success", "known_replay"}:
            done = resolve_reminder(
                pending["checkpoint"],
                "approve",
                pending["approval_target"],
                policy=policy,
                can_remind=True,
            )
            cases[case] = (
                resolve_reminder(
                    done["checkpoint"],
                    "approve",
                    pending["approval_target"],
                    policy=policy,
                    can_remind=True,
                )
                if case == "known_replay"
                else done
            )
        elif case == "refused":
            cases[case] = resolve_reminder(
                pending["checkpoint"], "refuse", policy=policy, can_remind=True
            )
        elif case == "cancelled":
            cases[case] = resolve_reminder(
                pending["checkpoint"], "cancel", policy=policy, can_remind=True
            )
        elif case == "changed_args":
            cases[case] = resolve_reminder(
                pending["checkpoint"],
                "approve",
                pending["approval_target"],
                pickup_at="18:00",
                policy=policy,
                can_remind=True,
            )
        elif case in {"failure_recovered", "attempt_exhausted"}:
            failed = resolve_reminder(
                pending["checkpoint"],
                "approve",
                pending["approval_target"],
                result="before_effect_error",
                policy=policy,
                can_remind=True,
            )
            cases[case] = resolve_reminder(
                failed["checkpoint"],
                "approve",
                pending["approval_target"],
                policy=policy,
                can_remind=True,
            )
        elif case == "unknown_after_effect":
            cases[case] = resolve_reminder(
                pending["checkpoint"],
                "approve",
                pending["approval_target"],
                result="response_lost",
                policy=policy,
                can_remind=True,
            )
        elif case in {"step_limit", "time_limit"}:
            cases[case] = resolve_reminder(
                pending["checkpoint"],
                "approve",
                pending["approval_target"],
                policy=policy,
                can_remind=True,
            )
        else:
            cases[case] = pending
    return {
        "disclaimer": (
            "Scripted proposals, canned answer, fixed public G-01 fixture, "
            "simulated milliseconds and effect counter; no LLM, retrieval, "
            "delivery, network or real time measurement."
        ),
        "cases": cases,
    }


def save_demo(output: Path) -> Path:
    """Create a fresh teacher output directory, refusing even an empty one."""
    output.mkdir(parents=True, exist_ok=False)
    demo = build_demo()
    trace = output / "trace.json"
    trace.write_text(json.dumps(demo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "checkpoint.json").write_text(
        json.dumps(json.loads(demo["cases"]["waiting"]["checkpoint"]), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return trace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(f"Teacher trace: {save_demo(args.output)}")
    print("All proposals and answers are authored; effects are local simulation only.")


if __name__ == "__main__":
    main()
