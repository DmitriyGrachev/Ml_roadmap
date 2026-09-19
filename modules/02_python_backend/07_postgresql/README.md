# 07 — PostgreSQL configuration and persistence

## Goal

Move database-specific learning to PostgreSQL without making a local database a prerequisite for ordinary API tests.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| A datasource selects PostgreSQL. | A settings value builds a PostgreSQL engine. |
| Database profiles isolate integration tests. | A `postgres` marker and environment variable opt in to integration tests. |

**Non-equivalence:** an environment variable is not a Spring profile; configuration remains ordinary validated Python data.

## Python model

Read `ROADMAP_POSTGRES_URL` only for opt-in checks. Keep generic repository behavior on SQLite and test PostgreSQL-only type and dialect behavior separately.

## Key concepts

- PostgreSQL URL
- environment-backed settings
- opt-in integration marker
- decimal and timezone behavior

## Example

When no URL is configured, a PostgreSQL test should skip with `Set ROADMAP_POSTGRES_URL and run: docker compose up -d postgres`.

## Exercises

The query exercise aggregates daily currency totals in SQL and includes a PostgreSQL-only verification.

## Self-check

1. Why is PostgreSQL opt-in here?
2. Which URL variable enables integration tests?
3. What belongs in a dialect-specific test?
4. Why not load all rows to aggregate?
5. How should a missing database be reported?

## Done when

You can run generic persistence tests without PostgreSQL and explain the opt-in command.
