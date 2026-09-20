# Stage 05 — SQLAlchemy and PostgreSQL

## Prerequisites

Complete [Stage 04](../04_fastapi/README.md) and review transaction/session boundaries, rollback, and
why database resources must be closed on both success and failure.

## Time box

Plan 75-90 minutes, including the SQLite feedback loop before optional Docker work.

## Editable surface

Edit only the three methods on `SqlAlchemyTransactionRepository` in
`banking_ai_lab/persistence.py`: `create_transaction`, `get_transaction`, and `list_transactions`.
The typed model, Decimal storage adapter, UTC restoration, engine, schema, and session factory are
complete. SQLite preserves Decimal text exactly for the fast learning loop, but its tagged storage
is not intended for SQL arithmetic or aggregate demonstrations. The opt-in PostgreSQL path uses
native NUMERIC semantics. `ROADMAP_POSTGRES_URL` is used only by the integration tests.

## Run the contracts

Run fast SQLite contracts first:

```powershell
uv run pytest projects/banking_ai_lab/tests/test_persistence.py -q -rx
```

For optional PostgreSQL, copy `.env.example` to `.env`, replace the local-only password, then run:

```powershell
cd projects/banking_ai_lab
docker compose up -d postgres
cd ../..
$env:ROADMAP_POSTGRES_URL = "postgresql+psycopg://banking_user:YOUR_LOCAL_PASSWORD@127.0.0.1:5432/banking_ai_lab"
uv run pytest -m postgres projects/banking_ai_lab/tests/test_postgres_integration.py -q -rs
```

To initialize the normal application schema explicitly and then start the app container, return to
the repository root and run:

```powershell
cd projects/banking_ai_lab
$env:BANKING_DATABASE_URL = $env:ROADMAP_POSTGRES_URL
uv run python -c "from banking_ai_lab.config import Settings; from banking_ai_lab.persistence import create_database_engine, create_schema; engine = create_database_engine(Settings().database_url); create_schema(engine); engine.dispose()"
docker compose up -d app
cd ../..
```

Schema creation is an explicit setup step; importing or constructing the FastAPI app never connects
to the database.

## Acceptance criteria

- Insert, get, filtered list, stable ordering, pagination, Decimal, and UTC round trips pass.
- SQLAlchemy text-column widths use the same shared limits enforced by the domain and HTTP DTOs.
- Duplicate inserts preserve existing data, translate the error, roll back, and close the session.
- Read/write failures propagate the original exception even when cleanup also fails.
- A configured unreachable PostgreSQL URL fails after bounded retries rather than skipping.
- PostgreSQL work happens in a unique schema that is removed even after a failing test.

## Hints

Keep a reference to the primary exception while performing cleanup. Add filters before ordering and
pagination. SQLite removes timezone metadata, so use the supplied row-to-domain mapping.

## Cleanup

From `projects/banking_ai_lab`, remove the opt-in service and its named data volume:

```powershell
docker compose down -v
```

Then remove `ROADMAP_POSTGRES_URL` from the shell and delete the local `.env` file.

## Completion checklist

- [ ] Every repository method passes independently against SQLite.
- [ ] Duplicate and controlled-failure cleanup contracts pass.
- [ ] PostgreSQL either passes or reports the exact documented opt-in skip.
- [ ] No password, `.env`, cache, or database file is committed.
