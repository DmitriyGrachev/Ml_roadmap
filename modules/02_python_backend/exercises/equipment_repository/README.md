# Store equipment with SQLAlchemy

Difficulty: Medium · Estimated time: 45–65 minutes

## Prerequisites

Module 02 SQLAlchemy persistence, transactions, exceptions, and pytest fixtures.
Know SQL inserts/selects and why query parameters must be bound separately.

## Requirements

Implement `EquipmentRepository.add` and `EquipmentRepository.list_all` in
`starter.py`. The immutable `Equipment` record, table, and schema creation are
provided. Use SQLAlchemy Core and the supplied caller-owned engine. Tests create
isolated local in-memory SQLite databases; no Docker or network is required.

- `add(Equipment(serial, name))` validates that both fields are nonempty strings
  without leading/trailing whitespace. Invalid values raise `ValueError` before
  an insert; include `equipment` in the message. Do not silently trim them.
- Add exactly one record and commit before returning `None`. Serial is unique
  and case-sensitive. A duplicate raises `ValueError`, retaining the original
  record; include `serial` in the error message. The repository must still accept later valid inserts.
- Use bound values; quotes and SQL-looking text are ordinary record data.
- `list_all()` returns a new list of immutable `Equipment` records ordered by
  serial ascending, or `[]` when empty. Read from the database on each call.
- A second repository on the same engine sees committed records. Repositories
  on distinct engines are independent. Changing a returned list cannot change
  stored data. Close connections/transactions but do not dispose the caller's
  engine. Do not keep a separate in-memory record cache.

## Example

```python
repository.add(Equipment("Z2", "Camera"))
repository.add(Equipment("A1", "Tripod"))
repository.list_all()
# [Equipment(serial="A1", name="Tripod"), Equipment(serial="Z2", name="Camera")]
```

## Edge cases and optional hints

Try duplicate serials, whitespace-only text, a name containing an apostrophe,
and an empty table. `engine.begin()` provides a transaction scope. Catch the
SQLAlchemy integrity error after the transaction has rolled back, and translate
the duplicate into the documented error. Use an explicit `ORDER BY`.

## Run and done when

From the repository root:

```powershell
uv run pytest modules/02_python_backend/exercises/equipment_repository -q -rx
```

Edit only `starter.py`. Done when all tests pass with zero xfails and data is
persisted across repository instances sharing the same engine.
