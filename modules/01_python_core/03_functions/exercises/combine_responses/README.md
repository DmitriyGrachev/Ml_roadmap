# Combine provider responses

## Goal

Align provider names with response objects while preserving order and supporting a one-shot response stream.

## Difficulty

Intermediate

## Estimated time

25–40 minutes

## Edit

Edit only `modules/01_python_core/03_functions/exercises/combine_responses/starter.py`.

## Requirements

- Accept provider names as a sequence and responses as any iterable, including a one-shot generator.
- Return frozen `IndexedProviderResponse` values in provider order.
- Use one-based indexes and preserve each original `ProviderResponse` object.
- Return `[]` when both inputs are empty.
- Raise `ValueError` containing `length` when responses are either shorter or longer than provider names.
- Traverse the response iterable no more than once.

## Acceptance criteria

Exact-length inputs are combined deterministically, both mismatch directions fail, and a response generator is never replayed.

## Run

`uv run pytest modules/01_python_core/03_functions/exercises/combine_responses -q -rx`

## Hints (optional)

Work with a single iterator and consider how you can distinguish exact exhaustion from an extra response.
