# Bounded exhibit assistant

Difficulty: **Medium**. Theme: answering questions using a public exhibit lookup.

## Goal

Implement `run_agent(model, tool, max_steps, max_tool_calls)` with finite counters, complete
observation history, and a deterministic audit trace.

## Java mental model

The model is a strategy object returning a proposal. The loop is the controller and keeps
the execution budget even when the strategy repeatedly requests the same action.

## Python model

Provided immutable records represent `CallTool`, `Finish`, `Observation`, `TraceEvent`, and
`RunResult`. The injected tool is the application's already-authorized single read operation;
there is no model-selected function name or external execution.

## Key concepts

Validate limits before any callback: `max_steps` is a positive integer and `max_tool_calls`
is a nonnegative integer, excluding booleans. Invalid values raise `ValueError` mentioning
`steps` or `tool`. Number model turns from 1. At each turn pass all successful observations
as a tuple to `model.propose`, then increment the model-step count.

For `Finish`, require nonblank `answer` or raise `ValueError` mentioning `answer`. Append
`TraceEvent(step, "finish", answer)` and return status `finished`, preserving answer text.
Finishing may occur with zero tool budget. For `CallTool`, require a nonblank `exhibit_id`
or raise `ValueError` mentioning `exhibit`. Append `(step, "proposal", exhibit_id)`.

If no tool budget remains, append `(step, "limit", "tools")` and return `tool_limit` without
calling the tool. Otherwise count the attempted call before invoking it. On success append
an `Observation(exhibit_id, text)` and `(step, "tool_result", text)`, preserving strings.
On `ToolFailure`, append `(step, "error", str(error))` and return `tool_error`; do not add an
observation or retry. Propagate other callback exceptions unchanged.

If the last permitted turn completes a tool call without finishing, append
`(max_steps, "limit", "steps")` and return `step_limit` without another model call.
For every non-finished status, `answer` is `None`. Always return actual model/tool counts,
successful observations, and the trace as tuples. Repeated IDs are allowed within budgets.
Tool text cannot change limits or cause direct execution. These count limits do not
interrupt a hung callback or enforce an elapsed-time deadline.

## Example

`CallTool("E-001"), Finish("A telescope.")` takes two model turns and one tool call. Its
trace is proposal, tool result, finish. With one permitted turn, the same first proposal
instead ends with `step_limit` after its tool result.

## Exercises

Implement the starter and run:

```powershell
uv run pytest modules/07_agents/03_bounded_agents/exercises/bounded_loop
```

The scripted model has finite fixtures; an unintended extra callback makes tests fail.

## Self-check

1. Does a proposed but blocked call consume tool budget?
2. Does a failed attempted call consume budget?
3. Why can zero tool budget still allow completion?
4. What happens to a programming error in the tool adapter?
5. What timeout protection remains outside this exercise?

## Done when

All tests pass with zero xfails, counters stay within policy, and the trace explains every
proposal, successful observation, failure, and stop.
