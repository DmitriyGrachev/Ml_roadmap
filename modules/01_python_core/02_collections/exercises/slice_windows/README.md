# Slice transaction windows

## Goal

Divide transaction IDs into consecutive, non-overlapping tuple windows.

## Difficulty

Beginner

## Estimated time

20–30 minutes

## Edit

Edit only `modules/01_python_core/02_collections/exercises/slice_windows/starter.py`.

## Requirements

- Require `size` to be positive; otherwise raise `ValueError`.
- Require every transaction ID to be a nonblank string; otherwise raise `ValueError`.
- Return full windows and retain a final partial window.
- Support sizes of one and sizes larger than the input; return `[]` for empty input.

## Acceptance criteria

Window boundaries are correct for every required size, validation remains active, and the tests pass.

## Run

`uv run pytest modules/01_python_core/02_collections/exercises/slice_windows -q -rx`

## Hints (optional)

Sequence slicing and a stepped `range` are relevant constructs for this exercise.
