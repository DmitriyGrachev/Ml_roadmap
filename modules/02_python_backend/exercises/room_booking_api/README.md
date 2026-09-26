# Build a room booking API

Difficulty: Medium · Estimated time: 50–75 minutes

## Prerequisites

Module 02 lessons on Pydantic validation, FastAPI routers, application factories,
HTTP error mapping, and API tests. Know half-open intervals from Python practice.

## Requirements

Implement `create_app()` in `starter.py`, returning a real `FastAPI` application.
Keep all state inside each created application; no database or server is needed.

- `POST /bookings` accepts JSON with `room`, `start`, and `end`. Room must be a
  string, trimmed before storing, and nonempty after trimming. Room comparisons
  are case-sensitive. Endpoints must be strict integers (no booleans, strings, or
  floats), satisfying `0 <= start < end <= 1440`. Missing or invalid fields give
  HTTP 422 and must not change state. Extra fields may be ignored.
- Endpoints represent minutes in one day and intervals are half-open: `[start,
  end)`. A booking that overlaps an existing booking in the same normalized room
  gets HTTP 409 and is not saved. Touching endpoints are allowed; other rooms
  may be booked simultaneously. Detect containment in both directions.
- A successful creation returns HTTP 201 and exactly
  `{"id": 1, "room": "Elm", "start": 60, "end": 90}`. IDs start at one and
  increase only for successful creations.
- `GET /bookings` returns HTTP 200 and a JSON list of those records in creation
  order, or `[]` for an empty app. Repeated reads do not change state.

## Example

```text
POST /bookings {"room": " Elm ", "start": 60, "end": 90}
201 {"id": 1, "room": "Elm", "start": 60, "end": 90}
POST /bookings {"room": "Elm", "start": 80, "end": 100}
409
POST /bookings {"room": "Elm", "start": 90, "end": 100}
201 {"id": 2, "room": "Elm", "start": 90, "end": 100}
```

## Edge cases and optional hints

Test an enclosing interval, the first/last minute of the day, invalid input
followed by a valid booking, and two independent apps. Pydantic strict integer
fields and a model validator can express the request contract. Compare both
interval boundaries when deciding overlap. Concurrency across workers, dates,
authentication, and cancellation endpoints are outside this exercise.

## Run and done when

From the repository root:

```powershell
uv run pytest modules/02_python_backend/exercises/room_booking_api -q -rx
```

Edit only `starter.py`. Done when all tests pass with zero xfails and each status
code represents a distinct validation, conflict, or successful creation result.
