# Typing

## Goal

Use modern annotations to document boundaries and express structural compatibility.

## Java mental model

Generic types and interfaces are familiar. A Python `Protocol` is structural: matching methods matter even without an explicit `implements` declaration.

## Python model

Use built-in generic forms such as `list[str]`, unions with `|`, `None` for optional values, `Literal` for a fixed value set, aliases for readable shapes, and protocols at external boundaries.

## Key concepts

Type hints support readers and static tools but do not enforce runtime validation themselves. Keep annotations precise where callers depend on a contract.

## Example

Run `uv run python modules/01_python_core/04_typing/example.py` to request a rate from an `ExchangeRateProvider` protocol.

## Exercises

The next coding task uses a payment-processor protocol without requiring inheritance.

## Self-check

1. What does `str | None` mean?
2. Are hints runtime validation?
3. What makes a protocol structural?
4. Why use a type alias?
5. When is `Callable` appropriate?
6. What contract does `Literal["ready", "failed"]` communicate?

## Done when

You can explain why a class can satisfy a protocol without naming it.
