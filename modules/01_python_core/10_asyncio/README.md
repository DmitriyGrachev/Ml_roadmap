# asyncio

## Goal

Use coroutines and `asyncio.gather` for independent I/O without confusing concurrency with CPU parallelism.

## Java mental model

Coroutines may resemble `CompletableFuture`. Python `asyncio` uses cooperative scheduling on an event loop; it is not a general replacement for threads or CPU parallelism.

## Python model

`async def` creates a coroutine, `await` yields while an awaitable is pending, and `gather` joins independent awaitables while retaining input order.

## Key concepts

Async helps when work spends time waiting on I/O. `asyncio.run` drives a top-level coroutine on an event loop, and `gather` can join independent awaitables without creating a thread for each one. This cooperative concurrency is not thread-based execution or CPU parallelism; CPU-heavy work needs a suitable process or thread strategy.

## Example

Run `uv run python modules/01_python_core/10_asyncio/example.py` to combine two different mocked study services into one dashboard.

## Exercises

- [Fetch quotes concurrently](exercises/fetch_quotes/README.md)

## Self-check

1. What does `async def` produce?
2. When does `await` yield control?
3. Does `gather` preserve input order?
4. Is asyncio CPU parallelism?
5. Which workloads benefit most?

## Done when

You can explain why concurrent I/O and parallel CPU work are different tools.
