# Data modeling

## Goal

Model domain values with dataclasses, composition, properties, and focused behavior.

## Java mental model

A frozen dataclass resembles a record. It is not a complete substitute for Java's inheritance and constructor-validation conventions.

## Python model

Use `@dataclass` for data-focused objects, composition for collaborating behavior, ABCs for necessary runtime abstraction, and protocols when shape is enough.

## Key concepts

`frozen=True` expresses immutable fields after construction. Properties can protect a useful derived invariant, but a plain attribute is clearer when no behavior is needed.

## Example

Run `uv run python example.py` to create a frozen ledger entry with a decimal amount.

## Exercises

Later practice models a validated payment value without hiding its domain rules.

## Self-check

1. When does a dataclass help?
2. What does `frozen=True` express?
3. Why prefer composition often?
4. When might a property help?
5. How does a protocol differ from an ABC?

## Done when

You can choose a small value object rather than a Java-style mutable POJO by default.
