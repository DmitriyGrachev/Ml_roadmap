# Bound concurrent station fetches

Difficulty: Medium · Estimated time: 50–75 minutes

## Prerequisites

Module 01 lessons 03 (callbacks), 06 (exceptions), 09 (pytest), and 10 (asyncio).
Know coroutine/task lifetimes, cancellation, and `try/finally` cleanup.

## Requirements

Implement `fetch_bounded(keys, fetch, limit)` in `starter.py`. A caller supplies an
async station lookup; tests supply event-gated lookups and need no network.

- Return one result per input occurrence in input order, even if completions are
  out of order. Duplicate keys trigger separate calls; do not deduplicate.
- Allow at most `limit` calls to `fetch` to be active at once. When enough keys
  exist, allow `limit` calls to begin before waiting for their results.
- A limit must be a positive integer (booleans/non-integers are invalid). Raise
  `ValueError` with `limit` in the message before calling `fetch` for invalid limits, even on empty input.
- Empty input returns `[]` without calling `fetch`. Do not mutate `keys`.
- If a lookup fails, propagate its original exception after cancelling and
  awaiting other unfinished lookup tasks, so their `finally` cleanup runs before
  this function exits. Do not leave background work running.
- Do not sleep, access real services, or add retries/timeouts. Test timeouts only
  guard against deadlocks; correctness checks use events and counts.

## Example

```python
async def lookup(station: str) -> str:
    return station.upper()


await fetch_bounded(["north", "south", "north"], lookup, 2)
# ["NORTH", "SOUTH", "NORTH"]
```

## Edge cases and optional hints

Try limit one, a limit larger than the input, duplicates, and one failing call
while another is waiting. A semaphore can protect the actual `await fetch(...)`.
Keep task references so that an error path can cancel and drain unfinished work.

## Run and done when

From the repository root:

```powershell
uv run pytest modules/01_python_core/exercises/bounded_fetch -q -rx
```

Edit only `starter.py`. Done when all tests pass with zero xfails, bounded work
can overlap, output order is stable, and failures leave no active lookups.
