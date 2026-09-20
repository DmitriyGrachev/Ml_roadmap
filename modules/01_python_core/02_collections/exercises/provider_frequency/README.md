# Count payment providers

## Goal

Count payment-provider names while retaining the order in which each distinct name first appears.

## Difficulty

Beginner

## Estimated time

15–25 minutes

## Edit

Edit only `modules/01_python_core/02_collections/exercises/provider_frequency/starter.py`.

## Requirements

- Accept any iterable of provider names, including a one-shot generator.
- Count names case-sensitively, so `Stripe` and `stripe` remain distinct.
- Preserve first-seen key order in the returned dictionary.
- Return `{}` for empty input.

## Acceptance criteria

Counts and insertion order match the input, case is preserved, and the tests pass.

## Run

`uv run pytest modules/01_python_core/02_collections/exercises/provider_frequency -q -rx`

## Hints (optional)

A dictionary preserves insertion order; `collections.Counter` is another counting tool worth comparing.
