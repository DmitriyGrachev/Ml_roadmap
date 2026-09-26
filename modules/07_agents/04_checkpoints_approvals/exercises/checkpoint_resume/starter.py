"""Resume a versioned local snapshot without confusing replay with exactly-once execution."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class PendingCall:
    call_id: str
    tool: str
    arguments: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Approval:
    workflow_id: str
    checkpoint_version: int
    call: PendingCall
    granted: bool


@dataclass(frozen=True)
class Receipt:
    call: PendingCall
    approved_version: int
    result: str


@dataclass(frozen=True)
class Checkpoint:
    workflow_id: str
    version: int
    pending: PendingCall | None
    receipts: tuple[Receipt, ...] = ()


class VersionConflict(RuntimeError):
    """The caller's expected version is stale."""


def resume_checkpoint(
    checkpoint: Checkpoint,
    approval: Approval,
    expected_version: int,
    execute: Callable[[PendingCall], str],
) -> Checkpoint:
    """Apply the approval/version/replay rules in README.md to a trusted snapshot."""
    raise NotImplementedError("Implement approved checkpoint resumption")
