# Authorized museum tool dispatch

Difficulty: **Medium**. Theme: museum catalogue lookup and workshop reservations.

## Goal

Implement `dispatch_tool(raw_proposal, permissions, executors)` to validate, authorize, and
dispatch one exact proposal through a trusted registry.

## Java mental model

Treat the input as an untrusted command DTO. The permission set and executor mapping are
application-owned dependencies, not fields the model can supply.

## Python model

The provided strict Pydantic models describe the envelope and two argument shapes.
Executors accept a `BaseModel` containing the correct validated subtype and return a string.
The function returns `ToolResult(call_id, tool, output)`.

## Key concepts

Apply these gates in order:

1. Parse the raw JSON with `Proposal.model_validate_json`. Only `lookup_exhibit` and
   `reserve_workshop` are allowed; even a registry containing another name cannot add it.
2. Validate the `arguments` object with `LookupArguments.model_validate` or
   `ReservationArguments.model_validate`, according to the selected tool.
3. Require the tool name in `permissions`; otherwise raise `PermissionError`.
4. Require a registered executor for that name; otherwise raise `LookupError`.
5. Call that executor exactly once with the validated model and return the result record.

Let `ValidationError` propagate for malformed JSON, extra fields, wrong types, and invalid
values. Exhibit IDs match `E-` plus three digits. Workshop IDs match `W-` plus three digits;
places is a strict integer from 1 through 4. No coercion, dynamic evaluation, fallback tool,
retry, or additional executor call is allowed. Propagate executor exceptions unchanged.
Preserve the output verbatim even when it contains instruction-like text; returning that
text does not authorize following it.

This exercise's permission granularity is the tool name. A production reservation would
also need resource-specific authorization, user approval where required, and idempotency.
Here every executor is a local fixture with no real reservation or external side effect.

## Example

`{"call_id":"call-1","tool":"lookup_exhibit","arguments":{"exhibit_id":"E-001"}}`
reaches the lookup executor only when the permission exists. Adding `"admin":true` to its
arguments fails schema validation before any executor runs.

## Exercises

Implement the starter boundary and run:

```powershell
uv run pytest modules/07_agents/02_tools_permissions/exercises/tool_dispatch
```

Tests cover both schemas, exactly one dispatch, denial, unknown tools, missing executors,
strict ranges/types, extra authority fields, and unchanged error/output propagation.

## Self-check

1. Who owns the registry?
2. Why is a model-supplied approval field invalid?
3. Why validate arguments before execution?
4. What does a returned instruction-like string authorize?
5. Where would resource-level policy be added?

## Done when

All tests pass with zero xfails and rejected proposals leave every executor untouched.
