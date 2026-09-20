# Decorators

## Goal

Wrap functions for cross-cutting behavior while preserving their callable contract.

## Java mental model

Decorators can feel like annotations or interceptors. Python decoration transforms a function object at definition time rather than relying on a container proxy.

## Python model

A decorator accepts a callable and returns a callable. `functools.wraps` preserves metadata that tools, tests, and logs need.

## Key concepts

Use `ParamSpec` when a generic decorator preserves arbitrary parameters. A logging decorator can record a call boundary without mixing logging into domain logic; avoid logging arguments that may contain secrets. Keep retry, logging, and timing policies explicit so failures and return values remain understandable.

## Example

Run `uv run python modules/01_python_core/08_decorators/example.py` to log label normalization while retaining the wrapped function's metadata.

## Exercises

- [Retry selected gateway failures](exercises/retry_gateway/README.md)

## Self-check

1. What does a decorator return?
2. Why use `wraps`?
3. When is a decorator appropriate?
4. What does `ParamSpec` preserve?
5. Why keep retry policy visible?
6. Which call details are safe and useful to log?

## Done when

You can add cross-cutting behavior without changing the decorated function's callers.
