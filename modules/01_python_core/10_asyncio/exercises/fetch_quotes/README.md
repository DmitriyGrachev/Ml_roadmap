# Fetch quotes concurrently

## Goal

Fan out independent asynchronous quote calls concurrently and return their values in input order.

## Difficulty

Intermediate

## Estimated time

25–40 minutes

## Edit

Edit only `modules/01_python_core/10_asyncio/exercises/fetch_quotes/starter.py`.

## Requirements

- Start one fetch coroutine for every symbol before waiting for any one result.
- Return values in the same order as the input symbols, regardless of completion order.
- Return `[]` without calling the fetcher for empty input.
- Propagate a child exception to the caller.
- Do not perform network I/O, sleep for timing, or use threads.
- Keep the supplied `QuoteFetcher` and function types.

## Acceptance criteria

Controlled events prove that all work starts before release, reverse completion does not reorder the
result, empty input is neutral, and a provider exception remains visible.

## Run

`uv run pytest modules/01_python_core/10_asyncio/exercises/fetch_quotes -q -rx`

## Hints (optional)

The standard library has a primitive that schedules multiple awaitables and retains argument order.
Concurrency here is cooperative I/O concurrency, not CPU parallelism.

## Self-check

1. What evidence shows that calls start concurrently?
2. Why is completion order different from result order in the test?
3. Does empty input create any child coroutine?
4. Which layer observes a child exception?
5. Why would a wall-clock speed assertion be weaker than controlled events?
