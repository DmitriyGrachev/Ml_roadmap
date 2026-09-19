# Exercise — Concurrent provider fan-out

## Goal

Fetch independent provider quotes concurrently while preserving the input gateway order.

## Difficulty

Intermediate.

## Estimated time

30–45 minutes.

## Requirements

- Implement `fetch_provider_quotes(gateways, request)` in `starter.py`.
- Start independent gateway I/O before waiting for any individual result.
- Preserve the input gateway order in the returned list.
- Return an empty list for no gateways.
- Propagate gateway exceptions and cancellation; do not convert them into a partial result.

## Acceptance criteria

- Event-gated tests show both gateway calls begin before either is released.
- No elapsed-time threshold is used to claim concurrency.
- The function does not call blocking I/O directly on the event loop.

## Commands

```powershell
uv run pytest modules/02_python_backend/05_async_endpoints/exercises/provider_fanout -q -rx
```

## Hints

- `asyncio.gather` preserves the order of awaitables it receives.
- Passing an empty iterable to the right concurrency primitive has a useful natural result.
- Do not catch broad `Exception`; cancellation and gateway failures must remain observable.
