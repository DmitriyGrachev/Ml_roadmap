# asyncio

## Goal

Use coroutines and `asyncio.gather` for independent I/O without confusing concurrency with CPU parallelism.

## Java mental model

Coroutines may resemble `CompletableFuture`. Python `asyncio` uses cooperative scheduling on an event loop; it is not a general replacement for threads or CPU parallelism.

## Python model

`async def` creates a coroutine, `await` yields while an awaitable is pending, and `gather` joins independent awaitables while retaining input order.

## Key concepts

Async helps when work spends time waiting on I/O. CPU-heavy work still needs an appropriate process or thread strategy; never infer concurrency from timing thresholds alone.

## Example

Run `uv run python example.py` to concurrently collect deterministic mocked LLM metadata.

## Exercises

Later practice coordinates controlled coroutines and checks ordered results plus exception propagation.

## Self-check

1. What does `async def` produce?
2. When does `await` yield control?
3. Does `gather` preserve input order?
4. Is asyncio CPU parallelism?
5. Which workloads benefit most?

## Done when

You can explain why concurrent I/O and parallel CPU work are different tools.
