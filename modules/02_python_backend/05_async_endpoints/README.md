# 05 — Async endpoints and I/O boundaries

## Goal

Use `async` to overlap independent I/O while keeping blocking work off the event loop.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| Reactive pipelines coordinate non-blocking work. | Coroutines yield while awaiting non-blocking I/O. |
| An executor runs blocking work elsewhere. | A thread or worker boundary owns blocking calls. |

**Non-equivalence:** `async def` does not make a synchronous database driver or HTTP client non-blocking.

## Python model

Use `async def` only when the endpoint awaits asynchronous I/O. Start independent gateway calls together with `asyncio.gather` and preserve an intentional result order.

## Key concepts

- coroutine scheduling
- cooperative I/O
- `asyncio.gather`
- cancellation propagation

## Example

The runnable support API exposes `GET /provider-statuses` as an actual `async def` route. Its
application factory receives status providers explicitly, and the route awaits the provider fan-out
in [`provider_status.py`](../examples/support_api/provider_status.py). The endpoint test proves both
providers start before the first resumes and that the HTTP response preserves configured order. A
CPU-heavy summarizer still belongs outside the request event loop.

## Exercises

The [provider-fanout exercise](exercises/provider_fanout/README.md) proves concurrency with event gates
rather than fragile timing thresholds.

## Self-check

1. What does `await` allow other tasks to do?
2. Why is a blocking call dangerous in `async def`?
3. When should `gather` be used?
4. How should cancellation behave?
5. Does async make CPU work parallel?
6. Where does the support endpoint compose its provider boundary?

## Done when

You can trace a real async endpoint through its fan-out function and name the I/O boundary for every
awaited operation.
