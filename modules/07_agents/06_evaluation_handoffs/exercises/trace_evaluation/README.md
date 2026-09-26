# Evaluate workflow traces

Difficulty: **Medium**. Theme: evaluating library and community-room assistant runs.

## Goal

Implement `evaluate_traces` so final-answer correctness, policy compliance, budget adherence,
and repeated tool work remain distinct measurable properties.

## Java mental model

Think of aggregating structured events with explicit denominators. Avoid reducing every
run to its final response and discarding the decisions that produced it.

## Python model

`Trace` carries externally judged `final_correct`, model-step counters, limits, and executed
`ToolEvent` records. Each event is an actual attempted execution, not a blocked proposal.
`arguments_key` is an application-supplied canonical identity for equivalent arguments.
The scorer neither parses model text nor executes tools.

## Key concepts

Require a nonempty tuple, nonblank unique exact run IDs, and valid counter metadata.
`steps` and `max_tool_calls` are nonnegative integers, while `max_steps` is positive;
booleans are excluded. Reject invalid run metadata with `ValueError` mentioning `trace`
or `run`; counter errors mention `steps` or `tool`. Require nonblank tool names and argument
keys, with errors mentioning `tool` or `argument`. Do not mutate inputs.

Compute the provided `TraceMetrics` fields using these policies:

- A successful run has `final_correct=True`, no unauthorized executed call, and no limit
  overrun. A recovered failed tool attempt does not independently disqualify success.
- `policy_violations` counts each call whose `authorized` field is false.
- `limit_violations` counts runs where `steps > max_steps` or
  `len(calls) > max_tool_calls`. Count a run once even if both limits were exceeded;
  equality is allowed.
- `redundant_calls` counts each repeated `(tool, arguments_key)` after its first occurrence
  within the same run, irrespective of outcome. Reset this tracking between runs.
- `total_tool_calls` includes successful and failed calls, including unauthorized ones.
  `tool_failure_rate` is failed calls divided by all calls, or `None` if there were none.
- `runs`, `successful_runs`, and `success_rate` use all supplied valid runs as denominator.

Do not mark repetition itself as a policy failure: it may reflect a legitimate retry.
Do not silently discard failed, unauthorized, or over-budget runs. The supplied correctness
labels are fixtures; this exercise evaluates the scorer, not live model quality.

## Example

One correct compliant run, one correct run with an unauthorized call, one correct run over
its limits, and one incorrect run give success rate 1/4. Two unauthorized calls count as
two policy violations; exceeding two limits in one run counts as one limit violation.

## Exercises

Implement the starter and run:

```powershell
uv run pytest modules/07_agents/06_evaluation_handoffs/exercises/trace_evaluation
```

Tests include no-call runs, exact limits, each limit exceeded independently, repeats across
and within runs, invalid metadata, recovered failures, multiple policy breaches, and
immutable inputs.

## Self-check

1. Why is the success rate stricter than answer accuracy?
2. What is the denominator of tool-failure rate?
3. Why reset redundancy tracking for each run?
4. Why can a recovered tool failure coexist with task success?
5. What evidence is missing from these local fixture labels?

## Done when

All tests pass with zero xfails and each metric's unit, denominator, and release implication
can be stated clearly.
