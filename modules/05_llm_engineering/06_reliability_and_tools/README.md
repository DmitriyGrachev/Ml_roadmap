# Reliability and tools

## Goal

Handle temporary provider failure within a finite budget and treat every proposed tool call
as untrusted input requiring application-owned permission.

## Java mental model

Use the same discipline as a remote-service client and command handler: classify errors,
bound attempts, preserve request identity, validate DTOs, authorize actions, then dispatch
an allowlisted operation.

## Python model

Use typed provider exceptions and an injected sleep function for deterministic retry tests.
Parse a tool proposal with Pydantic before passing typed arguments into a known function.
The example has one read-only operation on an in-memory book catalog.

## Key concepts

Retry only failures classified as transient by the adapter; invalid credentials, malformed
requests, and schema failures need different handling. Bound attempts and total elapsed
time. Configure per-attempt timeouts at the network boundary. A synchronous retry wrapper
cannot interrupt a provider call that never returns. Account for retries already performed
by an SDK so nested retry loops do not multiply load.

Production backoff often uses caps and jitter; the exercise injects a fixed schedule so
ordering is testable. A timeout may occur after remote work succeeded. Preserve the same
logical idempotency key across attempts, but do not assume a key prevents duplication unless
the provider supports and honors that contract. See [AWS retry guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html).

A model proposes tool names and arguments; the application grants permission and determines
which functions exist. Never execute model text with `eval`, `exec`, a shell, or dynamic
imports. Reject unknown tools, extra fields, and invalid identifiers. A model-supplied
`admin=true` is data, not authority. For actions with side effects, add application-managed
confirmation, idempotency, and audit records appropriate to the action. A full agent loop
is outside this lesson.

## Example

```powershell
uv run python modules/05_llm_engineering/06_reliability_and_tools/example.py
```

The application supplies `can_read` from its own authorization decision. The proposal can
name only `lookup_book`, and its identifier must match a constrained format. A missing valid
ID produces an error; the tool does not fabricate a book or run a path supplied by the model.

## Exercises

Implement [Bounded provider retries](exercises/bounded_retry/README.md), a Medium task with
temporary/permanent failures, exact delay accounting, and a stable request object.

## Self-check

1. Why must there be no sleep after the final failed attempt?
2. Does a stable key guarantee that a provider deduplicates work?
3. Where does permission come from, and can model output alter it?

## Done when

You can demonstrate bounded attempts and failure propagation, and trace a tool proposal
through permission checking, schema validation, and an allowlisted application operation.
