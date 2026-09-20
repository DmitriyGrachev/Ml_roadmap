# Build a configurable transaction filter

## Goal

Return a reusable predicate that combines transaction amount, currency, and optional business rules.

## Difficulty

Intermediate

## Estimated time

30–45 minutes

## Edit

Edit only `modules/01_python_core/03_functions/exercises/configurable_filter/starter.py`.

## Requirements

- Keep construction keyword-only and reject a negative `minimum` with `ValueError`.
- Accept the local `TransactionRow` shape without converting its `Decimal` amount through `float`.
- Treat the minimum as inclusive and `currencies=None` as no currency restriction.
- When currencies are supplied, accept only rows whose currency is in that configuration.
- Combine the amount and currency rules with the optional `predicate`.
- Capture an immutable snapshot of configuration so later caller mutation cannot change the returned predicate.

## Acceptance criteria

The returned callable applies every configured rule, supports unrestricted currencies, and remains stable after its caller changes an input collection.

## Run

`uv run pytest modules/01_python_core/03_functions/exercises/configurable_filter -q -rx`

## Hints (optional)

A closure can retain normalized configuration. A named inner function often communicates the business rule more clearly than a dense lambda.
