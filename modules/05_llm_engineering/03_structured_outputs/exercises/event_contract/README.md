# Museum event contract

Difficulty: **Medium**. Theme: extracting a museum event from a supplied announcement.

## Goal

Implement `parse_event(payload, allowed_venues, source_text)` so a generated event passes
both the provided schema and explicit application rules before it is accepted.

## Java mental model

DTO parsing is the first gate. The venue registry, chronological constraints, and evidence
check are business rules supplied by the caller, not authority granted by generated output.

## Python model

The provided frozen Pydantic `Event` model has strict types, forbidden extra fields, and
capacity bounds. Validate the raw string with `Event.model_validate_json`; return that
validated model after checking its semantic constraints. Do not use `model_construct`,
coerce fields, strip prose, repair JSON, or silently normalize extracted values.

## Key concepts

Required fields are `title`, `venue`, `starts_at`, `ends_at`, `seats`, and `evidence`.
`seats` must be an integer from 0 through 200 inclusive; numeric strings, booleans, and floats
are invalid. Unknown/missing fields, malformed JSON, and schema violations propagate
`pydantic.ValidationError`.

After schema validation enforce these rules with `ValueError` naming the relevant field:

1. `title` is nonblank and already trimmed: it must equal `title.strip()`.
2. `venue` exactly matches one of the caller's allowed venue strings.
3. Both datetime values have a non-`None` UTC offset, and `ends_at > starts_at` when compared
   as instants. Preserve their original timezone offsets; do not compare clock strings.
4. `evidence` is nonblank and is a case-sensitive, contiguous substring of `source_text`.

Time errors should mention `time`, `starts`, or `ends`. Other semantic messages mention
`title`, `venue`, or `evidence`. Strict JSON parsing accepts ISO datetime strings because
JSON has no native datetime value. The tests deliberately check that numeric coercions
remain forbidden. The evidence rule establishes presence, not entailment of every field.

## Example

A start at `10:00+02:00` and end at `09:00Z` on the same day is a one-hour event. A start
and end at the same instant must fail. A well-formed event at `"Unknown Museum"` fails if
that venue is absent from the application registry.

## Exercises

Implement the boundary and run:

```powershell
uv run pytest modules/05_llm_engineering/03_structured_outputs/exercises/event_contract
```

Exercise tests include strict capacity types, invalid/missing fields, extra commands,
timezone omission, cross-offset comparison, incorrect ordering, and unsupported evidence.

## Self-check

1. How can a quote be present without supporting the extracted number of seats?
2. Why must a naive datetime be rejected before comparison?

## Done when

All tests pass with zero xfails and you can identify which accepted-event claims still
need task-specific factual evaluation or human review.
