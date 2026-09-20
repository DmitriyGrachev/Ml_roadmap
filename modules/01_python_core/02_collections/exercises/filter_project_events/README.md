# Filter and project event records

## Goal

Select active events of allowed types and return only their IDs in input order.

## Difficulty

Beginner

## Estimated time

20–30 minutes

## Edit

Edit only `modules/01_python_core/02_collections/exercises/filter_project_events/starter.py`.

## Requirements

- Accept any iterable of the local `EventRow` type, including a one-shot generator.
- Require each event to have a nonblank string ID, string type, and boolean active flag.
- Include only active events whose type belongs to `allowed_types`.
- Return only IDs, preserve input order, and return `[]` when no event matches.

## Acceptance criteria

Filtering and projection happen at the typed boundary, validation remains active, and the tests pass.

## Run

`uv run pytest modules/01_python_core/02_collections/exercises/filter_project_events -q -rx`

## Hints (optional)

A list comprehension may combine a projection with readable filter conditions.
