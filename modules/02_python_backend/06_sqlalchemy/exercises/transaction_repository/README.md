# Exercise — Transaction repository

## Goal

Implement a small SQLAlchemy 2.x repository while keeping every session a bounded unit of work.

## Difficulty

Intermediate.

## Estimated time

45–60 minutes.

## Requirements

- Complete `SqlAlchemyTransactionRepository.add`, `get`, and `list_by_user` in `starter.py`.
- Receive the supplied `sessionmaker[Session]`; do not create an engine or global session.
- Open each session with a context manager, commit successful writes, roll back errors, and always close.
- Use SQLAlchemy 2 `select()` statements. `get` returns `None` for an unknown ID.
- Filter by user and order results by `timestamp`, then `id`.
- Keep amounts as `Decimal`. The supplied timestamp type normalizes values to UTC and restores
  timezone metadata that SQLite drops.

## Acceptance criteria

- Insert/get round trips preserve exact decimal values and return timezone-aware UTC timestamps.
- Duplicate IDs propagate `IntegrityError` after rollback; a failed write does not remove prior data.
- Database errors from `get` and `list_by_user` propagate unchanged after rollback.
- Successful and failing operations close their sessions.
- Invalid IDs, user IDs, currencies, amounts, and naive timestamps fail normally rather than becoming
  expected-incomplete results.

## Commands

```powershell
uv run pytest modules/02_python_backend/06_sqlalchemy/exercises/transaction_repository -q -rx
```

## Hints

- Put `commit()` inside `try`, call `rollback()` in `except`, and re-raise the original exception.
- `session.get(TransactionRecord, transaction_id)` is appropriate for the primary-key lookup.
- Use `.scalars().all()` for a typed list from a `select(TransactionRecord)` statement.
