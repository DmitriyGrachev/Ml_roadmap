# Resume an approved checkpoint

Difficulty: **Medium**. Theme: resuming a reviewed community-room reservation.

## Goal

Implement `resume_checkpoint(checkpoint, approval, expected_version, execute)` to enforce
exact approval matching and distinguish completed replay from new execution.

## Java mental model

This is an optimistic version check plus an immutable aggregate update. It models the
decision logic around persistence; it is not a transactional database implementation.

## Python model

The provided dataclasses are trusted, well-formed application snapshots. `PendingCall`
contains call ID, tool, and an ordered tuple of argument pairs. Equality is exact, including
argument order. `Receipt` remembers the approved call, its approval version, and result.
The injected `execute` is an application-owned dispatcher that rechecks current permissions.

## Key concepts

Apply the following ordered contract:

1. If `expected_version != checkpoint.version`, raise `VersionConflict` before all other
   checks, including replay. A stale caller must reread the current snapshot.
2. Require a granted approval for the same workflow; otherwise raise `PermissionError`.
3. If a receipt has the approval's call ID, require exact call equality and matching
   `approved_version == approval.checkpoint_version`. On mismatch raise `PermissionError`.
   On match return the **same checkpoint object**, with no execution/version increment,
   even if a different next action is pending.
4. Without a matching receipt, require a pending call or raise `ValueError` mentioning
   `pending`. Require `approval.checkpoint_version == checkpoint.version` and exact
   equality between the approval's call and the pending call; otherwise `PermissionError`.
5. Execute the pending call once. On success return a new checkpoint with version increased
   by one, no pending call, and a new receipt appended after existing receipts. Preserve
   workflow identity and result text. On any executor error, propagate it unchanged.

Never mutate the input snapshot or its records. Assume stored receipt call IDs are unique;
input-store validation is outside this task. A completed replay uses an old approval
version with a freshly read **current** expected snapshot version.

This callback example has a crash window between a remote effect and saving its receipt.
It does not provide exactly-once effects, concurrent atomic updates, durable storage, or
proof of the approver's identity. Those require application infrastructure and a trusted
approval source. An exception can mean the remote outcome is unknown.

## Example

Approval for version 4 executes once and creates version 5 plus a receipt. Rereading version
5 and replaying that same approval with expected version 5 returns the existing checkpoint.
Using stale expected version 4 raises a conflict; changing the room invalidates approval.

## Exercises

Implement the starter and run:

```powershell
uv run pytest modules/07_agents/04_checkpoints_approvals/exercises/checkpoint_resume
```

Tests check version order, changed approval fields, receipts, a different pending action,
exact replay identity, revoked or cross-workflow replay approval, single execution even
when the outcome is unknown, and failure preservation.

## Self-check

1. Why does replay require a current expected version?
2. Which changed fields invalidate approval?
3. Why must replay leave a later pending action alone?
4. What does the receipt prove about local state?
5. Which crash window can still duplicate an external action?

## Done when

All tests pass with zero xfails, denied or replayed requests never call the executor, and
you can describe the additional durability/concurrency work required in a real service.
