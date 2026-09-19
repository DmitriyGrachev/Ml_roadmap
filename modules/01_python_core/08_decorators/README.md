# Decorators

## Goal

Wrap functions for cross-cutting behavior while preserving their callable contract.

## Java mental model

Decorators can feel like annotations or interceptors. Python decoration transforms a function object at definition time rather than relying on a container proxy.

## Python model

A decorator accepts a callable and returns a callable. `functools.wraps` preserves metadata that tools, tests, and logs need.

## Key concepts

Use `ParamSpec` when a generic decorator preserves arbitrary parameters. Keep retry, logging, and timing policies explicit so failures and return values remain understandable.

## Example

Run `uv run python example.py` to time a document parser while retaining its original name.

## Exercises

Later practice adds a retry boundary with a specified retry count and preserved metadata.

## Self-check

1. What does a decorator return?
2. Why use `wraps`?
3. When is a decorator appropriate?
4. What does `ParamSpec` preserve?
5. Why keep retry policy visible?

## Done when

You can add cross-cutting behavior without changing the decorated function's callers.
