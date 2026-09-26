"""Approval binds an exact action; recorded replays do not re-execute it."""

from dataclasses import replace

import pytest

from roadmap_tools import exercise_call

from .starter import Approval, Checkpoint, PendingCall, Receipt, VersionConflict, resume_checkpoint

CALL = PendingCall("call-7", "reserve_room", (("room", "Studio"), ("slot", "10:00")))


def test_success_returns_new_version_and_receipt_without_mutating_snapshot() -> None:
    previous = Receipt(PendingCall("old", "lookup_room", (("room", "Studio"),)), 1, "available")
    checkpoint = Checkpoint("workflow-1", 4, CALL, (previous,))
    approval = Approval("workflow-1", 4, CALL, True)
    seen: list[PendingCall] = []

    def execute(call: PendingCall) -> str:
        seen.append(call)
        return "reservation-8"

    result = exercise_call(resume_checkpoint, checkpoint, approval, 4, execute)
    assert result == Checkpoint(
        "workflow-1", 5, None, (previous, Receipt(CALL, 4, "reservation-8"))
    )
    assert checkpoint == Checkpoint("workflow-1", 4, CALL, (previous,))
    assert seen == [CALL]


def test_recorded_replay_returns_snapshot_without_executor_or_version_increment() -> None:
    checkpoint = Checkpoint("workflow-1", 5, None, (Receipt(CALL, 4, "reservation-8"),))
    result = exercise_call(
        resume_checkpoint,
        checkpoint,
        Approval("workflow-1", 4, CALL, True),
        5,
        lambda _: pytest.fail("recorded replay must not execute"),
    )
    assert result is checkpoint


def test_stale_expected_version_wins_even_for_recorded_replay() -> None:
    checkpoint = Checkpoint("workflow-1", 5, None, (Receipt(CALL, 4, "reservation-8"),))
    with pytest.raises(VersionConflict):
        exercise_call(
            resume_checkpoint,
            checkpoint,
            Approval("workflow-1", 4, CALL, True),
            4,
            lambda _: pytest.fail("stale version"),
        )


@pytest.mark.parametrize(
    "approval",
    [
        Approval("other-workflow", 4, CALL, True),
        Approval("workflow-1", 3, CALL, True),
        Approval("workflow-1", 4, CALL, False),
        Approval("workflow-1", 4, replace(CALL, tool="delete_room"), True),
        Approval("workflow-1", 4, replace(CALL, call_id="call-8"), True),
        Approval("workflow-1", 4, replace(CALL, arguments=(("room", "Hall"),)), True),
    ],
)
def test_wrong_or_changed_approval_prevents_execution(approval: Approval) -> None:
    with pytest.raises(PermissionError):
        exercise_call(
            resume_checkpoint,
            Checkpoint("workflow-1", 4, CALL),
            approval,
            4,
            lambda _: pytest.fail("unauthorized execution"),
        )


def test_replay_rejects_same_id_with_changed_arguments_or_approval_version() -> None:
    checkpoint = Checkpoint("workflow-1", 5, None, (Receipt(CALL, 4, "reservation-8"),))
    for approval in (
        Approval("workflow-1", 4, replace(CALL, arguments=()), True),
        Approval("workflow-1", 5, CALL, True),
    ):
        with pytest.raises(PermissionError):
            exercise_call(
                resume_checkpoint, checkpoint, approval, 5, lambda _: pytest.fail("bad replay")
            )


def test_receipt_replay_does_not_consume_a_different_pending_action() -> None:
    pending = PendingCall("call-9", "reserve_room", (("room", "Hall"),))
    checkpoint = Checkpoint("workflow-1", 8, pending, (Receipt(CALL, 4, "reservation-8"),))
    result = exercise_call(
        resume_checkpoint,
        checkpoint,
        Approval("workflow-1", 4, CALL, True),
        8,
        lambda _: pytest.fail("replay must not execute next action"),
    )
    assert result is checkpoint
    assert result.pending == pending


@pytest.mark.parametrize(
    "approval",
    [Approval("workflow-1", 4, CALL, False), Approval("other-workflow", 4, CALL, True)],
    ids=["revoked-approval", "different-workflow"],
)
def test_recorded_replay_still_requires_current_authority(approval: Approval) -> None:
    checkpoint = Checkpoint("workflow-1", 5, None, (Receipt(CALL, 4, "reservation-8"),))
    with pytest.raises(PermissionError):
        exercise_call(
            resume_checkpoint,
            checkpoint,
            approval,
            5,
            lambda _: pytest.fail("unauthorized replay must not execute"),
        )


def test_absent_pending_call_and_absent_receipt_is_invalid_state() -> None:
    with pytest.raises(ValueError, match="pending"):
        exercise_call(
            resume_checkpoint,
            Checkpoint("workflow-1", 4, None),
            Approval("workflow-1", 4, CALL, True),
            4,
            lambda _: pytest.fail("no pending action"),
        )


def test_executor_failure_preserves_original_and_propagates() -> None:
    checkpoint = Checkpoint("workflow-1", 4, CALL)
    failure = RuntimeError("unknown remote outcome")
    seen: list[PendingCall] = []

    def failing(call: PendingCall) -> str:
        seen.append(call)
        raise failure

    with pytest.raises(RuntimeError) as caught:
        exercise_call(
            resume_checkpoint, checkpoint, Approval("workflow-1", 4, CALL, True), 4, failing
        )
    assert caught.value is failure
    assert checkpoint == Checkpoint("workflow-1", 4, CALL)
    assert seen == [CALL]
