# Stream NDJSON transactions lazily

## Goal

Turn newline-delimited JSON text into an iterator of transaction objects without reading ahead.

## Difficulty

Intermediate

## Estimated time

20–35 minutes

## Edit

Edit only `modules/01_python_core/07_iterators_generators/exercises/stream_transactions/starter.py`.

## Requirements

- Return an iterator and read no input while that iterator is created.
- Consume exactly one source line for each requested output row.
- Decode each line as JSON and yield its object unchanged.
- Let `json.JSONDecodeError` identify invalid JSON.
- Raise `ValueError` mentioning “object” when a decoded row is not a JSON object.
- Never materialize the input iterable or read ahead.

## Acceptance criteria

The tests observe zero reads at creation, one read per `next`, normal iterator exhaustion, and clear
errors for invalid JSON and non-object rows.

## Run

`uv run pytest modules/01_python_core/07_iterators_generators/exercises/stream_transactions -q -rx`

## Hints (optional)

A generator function delays body execution until iteration. `json.loads` already provides a
specific decoder exception; add only the domain check that it cannot know about.

## Self-check

1. What executes when the generator object is created?
2. How many source calls does one `next` trigger?
3. Which JSON values are not transaction objects?
4. Is the decoder exception still visible to the caller?
5. Would converting `lines` to a list violate the contract?
