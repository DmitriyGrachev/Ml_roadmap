# Minimize structured event logs

Difficulty: Medium. Estimated time: 45–75 minutes.

Prerequisites: mappings, copies, schema validation, and lesson 05.
Project a library service's local events onto a deliberately small telemetry schema.
No logs are sent or written. This is a field allowlist, not a universal personal-data detector.

## Contract

Implement `redact_events` in `starter.py`, preserving event order and returning a tuple
of `RedactedEvent(safe, dropped_fields)`:

| Level | Allowed field | Validation |
| --- | --- | --- |
| Top | `event` (required) | Exact string in `EVENT_NAMES` |
| Top | `timestamp_ms` (required) | Nonnegative integer; booleans invalid |
| Top | `request_id` (optional) | String length 1–64, nonblank after stripping; preserve exact text |
| Top | `attributes` (optional) | Mapping with the allowlisted fields below |
| Attributes | `route` | Exact string in `ROUTES`; never a raw URL or user-specific path |
| Attributes | `status_code` | Integer 100–599 inclusive; booleans invalid |
| Attributes | `latency_ms` | Finite nonnegative integer/float; booleans and strings invalid |
| Attributes | `model_version` | String length 1–32, nonblank after stripping; preserve exact text |

- Missing optional fields stay absent. Present `None` is invalid for every known field.
  Empty attributes remain `{}`. Reject a missing required field or any invalid known
  value with `ValueError` naming that field; never silently drop a bad known value.
- Remove every unknown top-level field and every unknown immediate attribute field.
  Count each removed field once in `dropped_fields`. Do not descend into an unknown
  field's value: dropping `payload={"token": ..., "email": ...}` counts as **one** removal.
  This schema has exactly two supported levels; it is not an arbitrary recursive filter.
- Preserve allowed values without string normalization. Create fresh top-level and
  attributes dictionaries; mutations of returned dictionaries must not affect input
  or results from another call. Do not alter the supplied sequence or mappings.
- Empty input returns `()`. Do not include removed values, key names, or raw events in
  errors or output. Report only the dropped count, not a diagnostic secret-bearing payload.

Allowed identifiers must still come from trusted application metadata. An email placed
inside a syntactically valid `request_id` cannot be detected by this exercise; an allowlist
reduces exposure but does not establish anonymity or compliance.

## Example

```python
redact_events(
    [
        {
            "event": "cache_hit",
            "timestamp_ms": 7,
            "prompt": "private",
            "attributes": {"route": "/books", "authorization": "secret"},
        }
    ]
)
# (RedactedEvent({"event": "cache_hit", "timestamp_ms": 7,
#                 "attributes": {"route": "/books"}}, dropped_fields=2),)
```

## TODO boundary and run

Implement `redact_events`; constants and output type are provided. Validation, projection,
counting, and independent copies are intentionally unsolved.

```powershell
uv run pytest modules/08_production_ai/05_privacy_security/exercises/redact_events -q -rx
```

Completion means all tests pass with zero xfails and you can name the remaining metadata,
access, retention, and logging-pipeline risks this local function does not address.
