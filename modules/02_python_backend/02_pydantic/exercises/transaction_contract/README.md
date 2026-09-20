# Exercise — Transaction contract

## Goal

Build a Pydantic 2 request model for a transaction API boundary.

## Difficulty

Intermediate.

## Estimated time

30–45 minutes.

## Requirements

- Complete `TransactionCreate` and `validate_transaction(payload)` in `starter.py`.
- Normalize lowercase or mixed-case currency to uppercase, then allow only `USD`, `EUR`, `GBP`, and `MDL`.
- Preserve `Decimal` amounts; reject zero and negative amounts.
- Reject blank merchants, naive timestamps, unknown currencies, and extra fields.
- Keep independent amount, currency, and timestamp errors attached to their own fields; a single
  model-level error is not field-specific enough for this API boundary.
- Add the documented example to the JSON Schema.

## Acceptance criteria

- `uv run pytest modules/02_python_backend/02_pydantic/exercises/transaction_contract -q -rx` reports passing tests after your implementation.
- Invalid payloads raise Pydantic validation errors; do not replace them with `None` or a generic error.
- A real FastAPI request with invalid amount, currency, and timestamp returns 422 locations
  `body.amount`, `body.currency`, and `body.timestamp`.
- Untouched starter code remains visibly expected-incomplete.

## Commands

```powershell
uv run pytest modules/02_python_backend/02_pydantic/exercises/transaction_contract -q -rx
```

## Hints

- Pydantic 2 uses `model_config`, field validators, and `model_json_schema()`.
- Normalize before checking the allowed currency set.
- `datetime.tzinfo` alone is not enough when an offset has no usable UTC value.
- Use field validators for independent rules. Reserve a model validator for a rule that compares
  multiple otherwise valid fields.
