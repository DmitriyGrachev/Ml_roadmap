# Stage 06 — Contract testing across boundaries

## Prerequisites

Complete [Stage 05](../05_postgresql/README.md), then review `exercise_call`, expected-incomplete
tests, deterministic fakes, and the difference between infrastructure and student boundaries.

## Time box

Plan 30-45 minutes for mutation checks and a complete project test pass.

## Editable surface

Study and extend focused cases in `test_api.py`, `test_persistence.py`, and
`test_postgres_integration.py`. Business implementations remain the named service and repository
methods from Stages 04 and 05; this stage adds no hidden production function.

## Run the contracts

From the repository root:

```powershell
uv run pytest projects/banking_ai_lab -q -rx
```

## Acceptance criteria

- Each unfinished method produces its own expected-incomplete result through `exercise_call`.
- Empty/no-op, reordered, double-call, swallowed-error, and leaked-detail mutants are rejected.
- Infrastructure tests never depend on a network service; PostgreSQL remains explicitly opt-in.
- The full project remains deterministic and leaves caller-owned data unchanged.

## Hints

Seed fakes and ORM rows directly so one unfinished method cannot hide another. Assert complete public
values, call counts, ordering, and exception identity—not only status codes or collection lengths.

## Cleanup

Temporary SQLite databases are removed by pytest. If PostgreSQL was started, run
`docker compose down -v` from `projects/banking_ai_lab` and delete the local `.env` file.

## Completion checklist

- [ ] Every student boundary has a separate focused test.
- [ ] Mutation probes fail for the intended assertion.
- [ ] Project and repository-wide pytest runs pass with only intentional skips/xfails.
- [ ] Ruff, format, mypy, lock, diff, and clean-status checks pass.
