# Search a library catalog

Difficulty: Medium

## Goal and prerequisites

Build a small read-only FastAPI endpoint over an in-memory book catalog.
Prerequisites: backend lessons 01–03 and 08, typed dataclasses, and stable sorting.
Estimated time: 60–90 minutes. No database, network service, or credentials are needed.

## Requirements

Implement `create_app(books)` and `GET /books`:

| Query | Default | Contract |
| --- | --- | --- |
| `q` | empty | Strip surrounding whitespace; case-insensitive substring in title OR author using `casefold()`; empty matches all |
| `available` | omitted | Optional boolean; filter by the exact availability when supplied |
| `sort` | `title` | Only `title` or `year`; title uses `casefold()`, year uses numeric order |
| `descending` | `false` | Boolean; reverse the key ordering while preserving input order for equal keys |
| `page` | `1` | Integer at least 1 |
| `page_size` | `10` | Integer from 1 through 50 |

- Apply both filters, then stable sorting, then pagination. Query parameters with
  invalid values return HTTP 422; FastAPI's standard boolean parsing is acceptable.
- Return HTTP 200 with exactly `total`, `page`, `page_size`, and `items`.
  `total` counts matches before pagination. Each item includes all five `Book`
  fields. An empty catalog, no matches, or a page beyond the end returns `items: []`.
- IDs, titles, and authors must be nonblank strings. IDs must be unique; `year`
  must be an integer in 1–9999, excluding booleans; `available` must be a boolean.
  Factory validation is supplied and raises `ValueError` for invalid catalog data.
- Each factory call owns a snapshot of its catalog. Later mutations of the
  caller's list cannot change the application. Do not reorder or mutate input.

## Example

Given `Book("b1", "Atlas", "A. Reed", 2010, True)` and
`Book("b2", "Gardens", "B. Hill", 2021, False)`,
`GET /books?q=reed&available=true&page_size=1` returns:

```json
{"total": 1, "page": 1, "page_size": 1, "items": [
  {"id": "b1", "title": "Atlas", "author": "A. Reed", "year": 2010, "available": true}
]}
```

## TODO boundary

Edit `starter.py`; implement `create_app` and any private helpers it needs. Keep
the public `Book` contract. Route creation and search behavior are intentionally
unsolved. Tests use `TestClient`; external HTTP requests are unnecessary.

## Run

```powershell
uv run pytest modules/02_python_backend/exercises/library_search -q -rx
```

Behavioral tests report `xfail` until the factory is implemented. Completion means
all behavioral tests pass without expected-incomplete results.
