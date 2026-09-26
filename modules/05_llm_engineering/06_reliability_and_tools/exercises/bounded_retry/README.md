# Bounded provider retries

Difficulty: **Medium**. Theme: requesting a short museum label from a provider interface.

## Goal

Implement `invoke_with_retry` so transient failures get a finite retry schedule and all
attempts preserve one logical request identity.

## Java mental model

Think of a small remote-service retry decorator with explicit exception classification and
an injected sleeper. The application controls the retry policy instead of catching every error.

## Python model

The `Provider` protocol, immutable `Request`, `TransientError`, and `PermanentError` are
provided. `sleep` is a callable receiving seconds; the tests inject a recorder, so no test
waits in real time or accesses a network.

## Key concepts

Validate the entire policy **before** calling the provider or sleeping. Require an integer
`max_attempts >= 1`, exactly `max_attempts - 1` supplied delays, and finite nonnegative
delay values. Invalid configuration raises `ValueError` mentioning `attempt` or `delay`.
Require nonblank `request.prompt` and `request.idempotency_key`; invalid values raise
`ValueError` mentioning `prompt` or `key`. Do not normalize valid requests.

Call `provider.complete` once initially. Return a successful string unchanged, including
whitespace, with no extra calls or sleeps. Catch only `TransientError`. If an attempt fails
and another is allowed, sleep for the corresponding supplied delay, then retry. Reuse the
exact same request object for every attempt. If the final allowed attempt fails, re-raise
that exception object and do not sleep again. Propagate permanent errors, other exceptions,
and sleeper failures immediately without another provider call.

`max_attempts` includes the initial call. A stable key is merely an application contract;
deduplication requires provider support. The exercise intentionally does not implement
network timeouts, a total deadline, random jitter, a circuit breaker, streaming, or tool
execution. Those require explicit adapter/service policy, and are not implied by bounded
attempt count. A hanging call still needs a timeout at its own boundary.

## Example

For three maximum attempts and delays `(0.1, 0.4)`, outcomes temporary error, temporary
error, success produce three calls and two sleeps. A permanent error on the first call
produces one call and no sleep. Exhaustion re-raises the third error without another sleep.

## Exercises

Implement the boundary and run:

```powershell
uv run pytest modules/05_llm_engineering/06_reliability_and_tools/exercises/bounded_retry
```

Tests assert call count, unchanged request identity, exact delay schedule, final exception
identity, early validation, success preservation, and propagation of sleeper interruption.

## Self-check

1. Why must a malformed policy fail before the first successful provider call?
2. Why might a timeout still incur usage or duplicate a side effect?

## Done when

All tests pass with zero xfails and you can distinguish bounded attempts, network timeouts,
idempotency support, and tool authorization as separate responsibilities.
