# Merge calendar intervals

Difficulty: Medium

## Goal and prerequisites

Combine a day's overlapping appointments into the smallest ordered list of busy
intervals. Prerequisites: collections, sorting, dataclasses, and pytest from lessons
02, 05, and 09. Estimated time: 40–60 minutes.

## Requirements

- An `Interval(start, end)` represents `[start, end)` in minutes after midnight.
  Both endpoints must be integers (booleans are invalid), with
  `0 <= start < end <= 1440`; raise `ValueError` otherwise.
- Accept unsorted input. Merge overlaps, containment, identical intervals, and
  touching endpoints: `[10, 20)` and `[20, 30)` become `[10, 30)`.
- Return a new list of `Interval` objects ordered by start. Keep gaps separate;
  the result must not contain intervals that still overlap or touch.
- An empty sequence returns `[]`; a single valid interval remains unchanged.
- Do not reorder or modify the caller's sequence. Repeated calls must agree.

## Example

```python
merge_intervals([Interval(630, 660), Interval(570, 610), Interval(600, 630), Interval(800, 840)])
# [Interval(start=570, end=660), Interval(start=800, end=840)]
```

## TODO boundary

Edit only `starter.py`. Implement `merge_intervals`; its input validation is
provided. Keep the immutable `Interval` contract. The merging algorithm is left
for you to write.

## Run

From the repository root:

```powershell
uv run pytest modules/01_python_core/exercises/calendar_intervals -q -rx
```

Behavioral tests are expected incomplete (`xfail`) until the TODO is implemented.
Completion means every behavioral test passes without an expected-incomplete result.
