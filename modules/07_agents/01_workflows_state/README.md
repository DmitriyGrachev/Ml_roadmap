# Workflow state

Подробное объяснение и G-01 trace: [теория 01](theory.md).

## Goal

Represent a task as explicit state and legal transitions before introducing model-selected
actions. Prefer a fixed workflow when the required steps are already known.

## Java mental model

A state record plus transition function resembles a state machine around command handlers.
An enum says which stages exist; transition rules say which moves are allowed. A queue or
graph scheduler answers a separate question: which independent tasks are ready now?

## Python model

Use a frozen dataclass for a snapshot and return a new value on transition. Keep the goal,
status, verified observations, pending work, budgets, and provenance explicit. Avoid hiding
essential state in a prompt string or a mutable global list.

## Key concepts

A deterministic workflow fixes the transition structure. A bounded agent delegates some
next-action choices to a model while retaining application constraints. Neither requires
free-form execution of model text. Separate planning from execution: a planned step is a
proposal, and marking it ready does not perform its action.

State updates should express observable facts. `tool_requested` and `tool_succeeded` are
different events; do not mark work complete before the result exists. Preserve failure
information so retries and handoffs can distinguish missing work from successful work.

For parallel tasks, define when dependency results become visible and how conflicting
updates combine. A deterministic tie breaker makes schedules reproducible. Cycles require
explicit stopping rules; a dependency planner that requires a DAG should reject them.
LangGraph's [graph overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
provides the framework mapping of state, nodes, and edges; lesson 05 uses it directly.

## Example

```powershell
uv run python modules/07_agents/01_workflows_state/example.py
```

An exhibit title moves from intake to review after validation, then to ready after approval.
Approval before validation raises an error. The original snapshot stays unchanged, and
`ready` does not publish anything.

## Exercises

Complete [Schedule a bounded workflow](../exercises/workflow_schedule/README.md). This
Medium task adds dependency validation, deterministic ready-task selection, concurrency
limits, and round limits. The example does not implement its graph scheduling algorithm.

## Self-check

1. What makes a transition legal beyond the existence of a status enum?
2. Why should a plan and an execution result have different representations?
3. When is a fixed workflow sufficient?
4. Why cannot a dependency finish halfway through a synchronous planning round?
5. What information should survive a failed transition?

## Done when

You can trace legal transitions and produce a bounded deterministic schedule without
executing the actions described by task data.
