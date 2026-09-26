# Module 02 — Production Python and FastAPI

## Goal

Build the mental model and habits for small, composable Python web services before applying them to the Banking AI Lab.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| `@SpringBootApplication` starts an application context. | An application factory returns a configured `FastAPI` instance. |
| `@RestController` groups HTTP handlers. | An `APIRouter` groups path operations. |

**Non-equivalence:** FastAPI does not create a Spring-style global container; application composition is ordinary Python code.

## Python model

Start with a working support-ticket API, then learn validation, composition, error boundaries, async I/O, persistence, tests, and packaging in sequence.

## Key concepts

- Pydantic 2 models define API contracts.
- Functions and small objects make dependencies visible.
- Async helps waiting on I/O; it does not make blocking code safe.
- Database sessions own a unit of work.

## Example

Run the support example tests from the repository root:

```powershell
uv run pytest modules/02_python_backend/examples -q
```

## Exercises

The later lessons introduce isolated payment-contract, router, error-mapping, fan-out, and persistence exercises. Keep their starter boundaries unsolved.

A standalone Medium exercise, [Search a library catalog](exercises/library_search/README.md),
adds neutral-domain practice with filtering, stable sorting, pagination, and API validation.

## Self-check

1. Which object represents an HTTP route group?
2. Where should an application factory create state?
3. Why is `Depends` not a global service locator?
4. What makes an API timestamp safe to exchange?
5. Which tests should require PostgreSQL?

## Done when

You can navigate the nine lessons, explain their order, and run the support example without Docker.

## Additional neutral-domain practice

- [Build a room booking API](exercises/room_booking_api/README.md) — validation, status codes, and overlap conflicts.
- [Serve a conditional document](exercises/conditional_cache/README.md) — content-derived ETags and HTTP 304.
- [Store equipment with SQLAlchemy](exercises/equipment_repository/README.md) — local transactions and repository queries.

These Medium exercises run locally and include automated behavioral tests.
