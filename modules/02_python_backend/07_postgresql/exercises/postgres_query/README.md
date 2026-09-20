# Exercise — Daily currency totals

## Goal

Build one SQLAlchemy 2.x aggregation that behaves consistently on SQLite and PostgreSQL.

## Difficulty

Intermediate.

## Estimated time

30–45 minutes.

## Requirements

- Complete `daily_currency_totals(session, day)` in `starter.py`.
- Treat `day` as a UTC half-open interval: midnight inclusive through the next midnight exclusive.
- Use SQL `sum`, `where`, `group_by`, and `order_by`; do not load transaction rows and aggregate in
  Python.
- Return immutable `CurrencyTotal` values sorted by currency with exact `Decimal` totals.
- Keep the function database-agnostic. Do not read environment variables in application code.

## Acceptance criteria

- Rows immediately outside the requested UTC day are excluded.
- Multiple records in one currency produce one exact total, and three currencies sort predictably.
- The emitted statement contains the aggregation, filtering, grouping, and ordering operations.
- The PostgreSQL test preserves `NUMERIC` and timezone-aware timestamp semantics when explicitly enabled.

## Commands

```powershell
uv run pytest modules/02_python_backend/07_postgresql/exercises/postgres_query -q -rx
uv run pytest -m postgres modules/02_python_backend/07_postgresql -q -rs
```

Without PostgreSQL, the marked check skips with:

`Set ROADMAP_POSTGRES_URL and run: docker compose up -d postgres`

Set only `ROADMAP_POSTGRES_URL` to opt in. A configured but unreachable or invalid database is a real
test failure, not a skip.

## Hints

- Compute `start` and `end` as timezone-aware UTC datetimes.
- Select the currency column and a labeled `sum(TransactionRecord.amount)` expression.
- Build `CurrencyTotal` instances from the returned rows; the database should do the arithmetic.
