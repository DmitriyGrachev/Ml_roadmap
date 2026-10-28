# Module 07 — Agents

## Goal

Build narrow, observable workflows whose model proposals remain subject to explicit state,
permission, approval, and resource limits. Learn when a fixed workflow is sufficient and
when a bounded model/tool loop adds useful flexibility.

## Prerequisites

Complete [LLM engineering](../05_llm_engineering/README.md) and
[RAG](../06_rag/README.md). Bring typed boundary design, validation, dependency injection,
evaluation, and Python collections. All work here runs offline using Python 3.12,
Pydantic 2, the repository's locked LangGraph and MCP SDK, and local fixtures.

## Java mental model

A workflow resembles an explicit state machine around service calls. A model can suggest
the next command, but the application retains the command handler, authorization checks,
transaction boundaries, and stop conditions.

## Python model

Use immutable state records, typed proposals, strict tool schemas, injected callables,
audit events, and versioned checkpoints. Lesson 05 uses real LangGraph nodes and an actual
MCP client/server over the SDK's in-process transport. No model, credentials, network port,
subprocess, hosted service, or external action is required. LangGraph tracing is disabled
inside its example without changing persistent environment settings.

## Key concepts

| Lesson | Outcome | Medium exercise |
| --- | --- | --- |
| [01 — Workflow state](01_workflows_state/README.md) | Represent legal transitions and ready work | [Schedule a bounded workflow](exercises/workflow_schedule/README.md) |
| [02 — Tools and permissions](02_tools_permissions/README.md) | Validate and authorize before dispatch | [Authorized museum tool dispatch](02_tools_permissions/exercises/tool_dispatch/README.md) |
| [03 — Bounded agents](03_bounded_agents/README.md) | Stop model/tool loops with an auditable result | [Bounded exhibit assistant](03_bounded_agents/exercises/bounded_loop/README.md) |
| [04 — Checkpoints and approvals](04_checkpoints_approvals/README.md) | Bind approval and replay to exact work | [Resume an approved checkpoint](04_checkpoints_approvals/exercises/checkpoint_resume/README.md) |
| [05 — LangGraph and MCP](05_langgraph_mcp/README.md) | Separate orchestration from tool interoperability | Run the actual local framework example |
| [06 — Evaluation and handoffs](06_evaluation_handoffs/README.md) | Score traces and preserve context at handoff | [Evaluate workflow traces](06_evaluation_handoffs/exercises/trace_evaluation/README.md) |

A saved checkpoint is not a guarantee of exactly-once external effects. A discovered tool
is not a permission grant. A correct final answer is not evidence that the workflow acted
within policy. These distinctions are the organizing constraints of the module.

## Example

Начните с [теории 01](01_workflows_state/theory.md), затем идите по урокам 02–06.
[Сквозной teacher walkthrough](walkthrough.py) даёт один офлайн trace по правилу G-01;
ответы и proposals в нём заранее написаны, а эффект напоминания только симулирован.
Запуск: `.venv/Scripts/python.exe -m modules.07_agents.walkthrough --output <new-directory>`.
Папка должна ещё не существовать. Теория дополняет прежние примеры и задания.

From the repository root:

```powershell
uv run python modules/07_agents/05_langgraph_mcp/example.py
uv run pytest modules/07_agents
uv run mypy -p modules.07_agents
```

Each lesson has a standalone `example.py`. Its fixtures are deterministic and demonstrate
application mechanics rather than real-model reasoning, injection resistance, or quality.

## Exercises

Complete the eight Medium tasks across the core and additional practice maps. The original
planner remains available unchanged. The other seven exercises provide typed boundaries
and explicit behavioral tests;
`NotImplementedError` is converted to expected-incomplete output by `exercise_call`.
Completion requires passing tests with zero xfails, not merely a green starter-suite exit.

## Self-check

1. Where does authority remain when a model proposes a tool call?
2. What differs between a graph transition, a checkpoint, and an external effect?
3. Which limits can a pre-step check enforce, and which need transport support?
4. How does changing a pending action invalidate prior approval?
5. What can a trace reveal that final-answer scoring cannot?

## Done when

All six examples run, the eight implemented exercise suites pass without xfails, and you
can explain tool permissions, bounded execution, approval/replay semantics, LangGraph/MCP
roles, and the limitations of local contract tests.

## Additional practice map

These three independent exercises extend the five core tasks above without replacing them.

| Exercise | Focus | Estimate |
| --- | --- | --- |
| [Validate a museum tool plan](exercises/plan_validation/README.md) | Dependency DAG and capability validation before execution | 45–70 min |
| [Prepare a permission-filtered library handoff](exercises/handoff_packet/README.md) | Required context, permissions, and deterministic truncation | 45–70 min |
| [Route a museum tool result](exercises/tool_result_routing/README.md) | Typed outcomes and bounded retry recommendations | 30–50 min |
