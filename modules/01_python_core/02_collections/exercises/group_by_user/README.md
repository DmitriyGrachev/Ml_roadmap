# Group transaction amounts by user

## Goal

Build a dictionary of each user's transaction amounts while preserving input order.

## Difficulty

Beginner

## Estimated time

25–35 minutes

## Edit

Edit only `modules/01_python_core/02_collections/exercises/group_by_user/starter.py`.

## Requirements

- Accept any iterable of `(user_id, amount)` tuples, including a one-shot generator.
- Require nonblank string user IDs and `Decimal` amounts; otherwise raise `ValueError`.
- Preserve first-seen user order and transaction order within each user's list.
- Keep amounts as `Decimal` values and return `{}` for empty input.

## Acceptance criteria

The output order is deterministic, decimal values remain exact, validation remains active, and the tests pass.

## Run

`uv run pytest modules/01_python_core/02_collections/exercises/group_by_user -q -rx`

## Hints (optional)

`dict.setdefault` can create a user's list on first encounter.
