# Stage 04 — FastAPI service layer

## Prerequisites

Complete [Stage 03](../03_pandas_analysis/README.md), then review immutable `Transaction` values and
the difference between HTTP validation, application services, and repositories.

## Time box

Plan 60-90 minutes, followed by a short contract review.

## Editable surface

Edit only these `TransactionService` methods in `banking_ai_lab/service.py`:

- `create_transaction`
- `get_transaction`
- `list_transactions`

The Settings, DTO, router, exception-handler, and application-factory plumbing is complete.

## Run the contracts

From the repository root:

```powershell
uv run pytest projects/banking_ai_lab/tests/test_api.py -q -rx
```

## Acceptance criteria

- POST and GET responses contain every transaction field with stable JSON types.
- Missing and duplicate records become safe 404 and 409 responses.
- List results preserve timestamp/ID order and pass explicit filters and pagination.
- Invalid amounts, currencies, timestamps, offsets, and limits never call the service.
- Unrelated exceptions remain visible in tests and generic in production-mode responses.

## Hints

Delegate one operation at a time through the repository protocol. Treat `None` from the repository
as a domain event at the service boundary. Do not catch exceptions that the contract does not name.

## Cleanup

This stage uses in-memory fakes and temporary paths, so it leaves no service or database to stop.

## Completion checklist

- [ ] Each service method passes independently.
- [ ] Expected-incomplete results disappeared only for methods you completed.
- [ ] Health and validation infrastructure still passes normally.
- [ ] Ruff and mypy pass for the project.
