# Validate a museum tool plan

Difficulty: Medium. Estimated time: 45–70 minutes.

Prerequisites: dictionaries, sets, directed graphs, typed dataclasses, and lessons
[01 — Workflow state](../../01_workflows_state/README.md) and
[02 — Tools and permissions](../../02_tools_permissions/README.md).

A museum assistant proposes a list of tool steps. Review its structure and permissions
before anything can run. This exercise validates a proposal; it does not choose a schedule,
execute tools, infer approval, or prove the proposed work is useful.

## Contract

Implement `validate_plan(steps, allowed_capabilities, max_steps)` in `starter.py`.
Inputs use the supplied types. Dataclasses intentionally do not validate themselves.

1. `max_steps` must be an integer excluding booleans, in `[1, 100]`. A plan must contain
   between one and `max_steps` steps, inclusive.
2. Step IDs and capabilities must be strings of 1–80 characters with no leading or
   trailing whitespace. Internal whitespace is allowed. IDs must be unique; comparisons
   are case-sensitive and must not normalize names.
3. A dependency names a step anywhere in the proposal, including a later declaration.
   Reject unknown IDs, self-dependencies, repeated dependencies within a step, and cycles
   anywhere in the graph. Shared prerequisites and disconnected acyclic components are valid.
4. Validate all structure before checking permissions. Any structural violation raises
   `ValueError`. Only after structure is valid, require every step's capability to belong
   to the application's `allowed_capabilities`; otherwise raise `PermissionError`.
   The provided capability set is trusted policy, not a field the proposal may override.
5. On success return all step IDs as a tuple in their original declaration order.
   Do not reorder dependencies, mutate inputs, or run any action. Error message wording
   is not prescribed. Repeated calls with equal inputs must give equal results.

## Example

`(PlanStep("describe", "write", ("lookup",)), PlanStep("lookup", "read"))`
with permissions `frozenset({"read", "write"})` and `max_steps=2` returns
`("describe", "lookup")`. This declaration order is deliberately not execution order.
Changing `lookup` to depend on `describe` introduces a cycle and raises `ValueError`.

## TODO boundary and run

Implement `validate_plan`, including graph validation. No graph algorithm is supplied.

```powershell
uv run pytest modules/07_agents/exercises/plan_validation -q -rx
```

Optional hints: compare declared IDs with dependency IDs first; a graph traversal needs
to distinguish a currently active path from an already completed node. Visit every component.

Done when the focused tests pass with zero xfails and you can explain why a valid DAG is
neither authorization for external effects nor a guarantee that a proposed plan is correct.
