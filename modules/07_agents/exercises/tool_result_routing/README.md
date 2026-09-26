# Route a museum tool result

Difficulty: Medium. Estimated time: 30–50 minutes.

Prerequisites: typed unions, conditional precedence, and
[03 — Bounded agents](../../03_bounded_agents/README.md).

A museum catalog workflow receives a completed tool result. Decide whether to finish,
request one more attempt, or hand off to a person. This pure decision function neither
calls tools nor updates counters, waits, changes permissions, or performs a handoff.

## Contract

Implement `route_result(result, attempts, max_attempts, remaining_calls)`.

1. `attempts` counts already completed attempts, including this result. It is an integer
   excluding booleans, from one through `max_attempts`. `max_attempts` is an integer
   excluding booleans in `[1, 10]`. `remaining_calls` counts calls still available **after**
   the completed attempt and is an integer excluding booleans in `[0, 100]`.
2. Status is exactly `success`, `transient`, `permanent`, or `permission-denied`.
   Validate all counters and status before routing, even for success. Invalid values
   raise `ValueError`; error message wording is not prescribed. Other inputs use their
   declared types. Payload text is opaque data and may be empty.
3. Success returns `Route("finish", "success", result.payload)` regardless of remaining
   limits. Payload content never changes a status or grants permission.
4. A permanent or permission-denied result returns action `handoff`, with that status as
   its reason and `output=None`, regardless of resource counters.
5. For a transient result, use the first matching rule:
   - If `attempts == max_attempts`, hand off with reason `attempts-exhausted`.
   - Otherwise if `remaining_calls == 0`, hand off with reason `budget-exhausted`.
   - Otherwise return action `retry` and reason `transient`.
   All these results have `output=None`; error payloads are not forwarded as successful output.
6. Do not mutate inputs. Repeated calls with equal inputs return equal `Route` values.
   The caller must separately enforce the recommendation at the next execution boundary.

## Example

`ToolResult("transient", "catalog busy")`, `attempts=2`, `max_attempts=3`, and
`remaining_calls=1` returns `Route("retry", "transient", None)`. The same failure after
attempt three returns `Route("handoff", "attempts-exhausted", None)`.

## TODO boundary and run

Implement `route_result`, including counter validation and the ordered policy.

```powershell
uv run pytest modules/07_agents/exercises/tool_result_routing -q -rx
```

Optional hint: validation and routing have different jobs. Keep success and nonretryable
statuses separate from the transient-limit checks.

Done when the focused tests pass with zero xfails and you can explain why a retry decision
does not provide backoff, idempotency, exactly-once effects, or enforcement by itself.
