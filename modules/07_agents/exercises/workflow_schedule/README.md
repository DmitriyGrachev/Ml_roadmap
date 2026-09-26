# Schedule a bounded workflow

Difficulty: Medium

## Goal and prerequisites

Plan a dependency graph in deterministic rounds with explicit concurrency and
round limits. Prerequisites: sets, dictionaries, dataclasses, graph traversal,
and pytest. No model or completed agent course is needed. Estimated time: 60–90 minutes.

This exercise is an offline planner. A `Task` is data; scheduling never runs tools,
contacts services, invokes callbacks, or performs any task's described action.

## Requirements

- IDs must be nonempty strings without outer whitespace and unique across tasks.
  Dependencies must name existing tasks, contain no duplicates per task, and
  exclude the task itself. These structural validations are provided.
- `max_parallel` and `max_rounds` must be positive integers, excluding booleans.
  Invalid arguments raise `ValueError`, including on an empty graph.
- Reject every cyclic graph with `ValueError` whose message contains `cycle`.
  Validate the **whole graph** before planning; a disconnected cycle is invalid
  even if the round budget would expire before those tasks could be considered.
- At the beginning of each round, identify unplanned tasks whose dependencies
  completed in earlier rounds. Choose up to `max_parallel` ready IDs in
  lexicographic order. All tasks in a round complete together at its end; a child
  cannot run in its parent's round.
- Stop when all tasks finish or after `max_rounds` rounds. Return a frozen
  `Schedule` with a tuple of round tuples and lexicographically sorted `unfinished`
  IDs. Do not pad with empty rounds. Empty input produces `Schedule((), ())`.
- Do not modify input or use input order as a tie breaker. Any permutation of the
  same valid task definitions must produce the same schedule.

## Example

```python
schedule_workflow(
    [Task("publish", ("edit",)), Task("edit", ("read",)), Task("read"), Task("audit")],
    max_parallel=2,
    max_rounds=2,
)
# Schedule(rounds=(("audit", "read"), ("edit",)), unfinished=("publish",))
```

## TODO boundary

Implement `schedule_workflow` in `starter.py`. Frozen types and local validation
are provided. Cycle detection, ready-task selection, and bounded scheduling are
intentionally unsolved; private helpers are allowed.

## Run

```powershell
uv run pytest modules/07_agents/exercises/workflow_schedule -q -rx
```

The unfinished boundary reports expected-incomplete (`xfail`) tests. Completion
means all behavioral tests, including cycle checks, pass without those results.
