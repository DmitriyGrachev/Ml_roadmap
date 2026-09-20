# Retry selected gateway failures

## Goal

Complete a parameterized decorator that retries only declared transient failures while preserving
the wrapped callable's interface and metadata.

## Difficulty

Intermediate

## Estimated time

30–45 minutes

## Edit

Edit only `modules/01_python_core/08_decorators/exercises/retry_gateway/starter.py`.

## Requirements

- Treat `attempts` as the total permitted calls and reject non-positive values.
- Retry only exceptions matching `retry_on`.
- Return immediately after the first successful call.
- After exhaustion, re-raise the last retryable exception unchanged.
- Propagate every non-retryable exception after one call.
- Do not sleep, log, or add backoff; those concerns are outside this exercise.
- Preserve name, documentation, arguments, and return typing with `functools.wraps`.

## Acceptance criteria

The tests pin exact call counts on recovery, exhaustion, and a non-retryable failure, identify the
same propagated exception objects, and preserve wrapped metadata.

## Run

`uv run pytest modules/01_python_core/08_decorators/exercises/retry_gateway -q -rx`

## Hints (optional)

Keep the decorator factory, decorator, and wrapper as separate scopes. An exception tuple is valid
in an `except` clause, and a bare `raise` preserves the current exception.

## Self-check

1. Does `attempts=1` call the operation once?
2. Which exception triggers another attempt?
3. Which exception object escapes after exhaustion?
4. Can a non-retryable error cause a second call?
5. What metadata does `functools.wraps` preserve?
