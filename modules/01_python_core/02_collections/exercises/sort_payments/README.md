# Sort payments with multiple keys

## Goal

Return payment rows in a deterministic business order without changing the caller's collection.

## Difficulty

Intermediate

## Estimated time

30–45 minutes

## Edit

Edit only `modules/01_python_core/02_collections/exercises/sort_payments/starter.py`.

## Requirements

- Accept any iterable of the local `PaymentRow` type, including a one-shot generator.
- Require a nonblank string `id`, a `Decimal` amount, and a timezone-aware `datetime` timestamp.
- Sort by descending amount, then ascending timestamp, then ascending ID.
- Return a new list, leave a list input unchanged, and return `[]` for empty input.

## Acceptance criteria

All three keys participate in ordering, invalid rows fail before the unfinished boundary, and the tests pass.

## Run

`uv run pytest modules/01_python_core/02_collections/exercises/sort_payments -q -rx`

## Hints (optional)

`sorted` returns a new list and accepts a key function; tuples compare field by field.
