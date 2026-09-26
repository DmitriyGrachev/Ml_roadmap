# Checkpoints and approvals

## Goal

Resume paused work only when the expected snapshot and exact approved operation still
match, while distinguishing replay protection from exactly-once external execution.

## Java mental model

A checkpoint resembles versioned aggregate state. Optimistic concurrency compares the
version read by the caller with the stored version before accepting a change. Approval is
an authorization artifact for a particular proposed command, not a general boolean flag.

## Python model

Use immutable snapshots, exact pending-call records, explicit approval metadata, and
completed-call receipts. A successful update creates a new version. A replay of a recorded
call can return the recorded snapshot without invoking the tool again.

## Key concepts

Bind approval to workflow identity, state version, call ID, tool, and arguments. Changing
the destination, amount, resource, or requested operation invalidates the original approval.
The approval's origin and the caller's current permissions also need application verification.
A content digest can identify an approval target; it does not authenticate the approver.

A checkpoint persists progress, not a transaction across arbitrary remote tools. A process
can crash after a tool commits but before a receipt is saved. Replaying that checkpoint may
duplicate the effect. Use provider-supported idempotency, durable operation records, or a
transactional outbox where appropriate. A local frozen dataclass cannot make two workers'
updates atomic; a real store needs compare-and-swap or a transaction.

LangGraph [persistence](https://docs.langchain.com/oss/python/langgraph/persistence) saves
graph state through checkpointers. Its [interrupt documentation](https://docs.langchain.com/oss/python/langgraph/interrupts)
explains resumption and node re-execution, so operations before an interrupt must be safe
to repeat. The exercise teaches a small explicit contract rather than reproducing a full
durable workflow engine.

## Example

```powershell
uv run python modules/07_agents/04_checkpoints_approvals/example.py
```

Canonical JSON gives two equivalent argument dictionaries the same fingerprint; changing
the room changes the fingerprint. No approval is granted and no action is executed.

## Exercises

Implement [Resume an approved checkpoint](exercises/checkpoint_resume/README.md), a Medium
task covering stale versions, exact approval matching, recorded replay, and failure preservation.

## Self-check

1. Which fields must an approval bind?
2. Why should a stale reader reread before replaying?
3. What happens in the crash window between an external effect and its receipt?
4. Does a hash authenticate the approving person?
5. Why does concurrent persistence require more than an in-memory version check?

## Done when

Stale or changed approvals cannot execute, recorded replay performs no duplicate call,
and you can explain why the remaining crash window prevents an exactly-once claim.
