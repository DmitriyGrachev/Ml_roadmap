# Assemble a museum answer stream

Difficulty: Medium

## Prerequisites and time

Python sorting, strings, dataclasses, and the Module 05 provider-boundary lesson. Estimated time: 60–75 minutes.

## Goal and TODO boundary

Implement `assemble_stream` for a finite batch of events captured from one
synthetic museum-answer stream. Basic field validation is supplied; structural
validation, assembly, and status are TODOs. No async framework or provider is needed.

## Contract

- The requested `stream_id` is a nonblank string. Every `StreamEvent` has that
  exact stream ID, a nonnegative integer sequence (not bool), a kind of
  `"delta"`, `"done"`, or `"error"`, and string text.
- Deltas may contain any text, including empty strings. Done text must be exactly
  empty. Error text must be nonblank and is preserved exactly.
- Events may arrive out of order. Sort by sequence; their sequence numbers must
  be exactly `0, 1, ..., n-1`. Reject duplicate numbers even when the events are
  identical. Reject gaps, a missing zero, or mixed stream IDs.
- A done or error event is terminal. At most one terminal event may occur and it
  must be last in sequence order. Reject any event after a terminal.
- Concatenate delta text exactly, without stripping whitespace or inserting
  separators. Return `StreamResult(text, status, error)`.
- A final done means status `"complete"` and error `None`; a final error means
  status `"error"`, its message in error, and accumulated partial delta text.
  No terminal means `"incomplete"` with error `None`.
  Empty input returns `StreamResult("", "incomplete", None)`.
- All malformed field or structural inputs raise `ValueError`; do not return
  partial success for malformed streams. Do not mutate events or retain state.

## Hand-calculated example

Events supplied as `(2, done, "")`, `(1, delta, " café!")`,
`(0, delta, "Museum")` assemble to `"Museum café!"` with complete status.
Replacing event 2 with `(2, error, "unavailable")` keeps the same partial
text, sets error status, and stores the message separately.

## Optional hints

Validate the sequence before building the result. Arrival order and logical
sequence order are deliberately different.

## Run and completion

From the repository root:

```powershell
uv run pytest modules/05_llm_engineering/exercises/stream_assembly -q -rx
```

Implement only the named function in `starter.py`; keep the tests intact. The
untouched algorithm raises `NotImplementedError` and appears as expected-incomplete
(`xfail`) through `roadmap_tools.exercise_call`. Supplied validation checks pass
already. Completion requires every test to pass with **zero xfails**.
