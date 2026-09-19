# Exercise — Payment error mapping

## Goal

Turn expected payment domain exceptions into stable, safe API responses.

## Difficulty

Intermediate.

## Estimated time

25–40 minutes.

## Requirements

- Implement `register_payment_exception_handlers(app)` in `starter.py`.
- Map `PaymentNotFound` to 404 and `PaymentConflict` to 409.
- Return exactly `code`, `message`, and `request_id` for each mapped error.
- Read `X-Request-ID`; if absent, use the deterministic fallback `request-id-not-provided`.
- If you add logs, use structured fields and never log card or account data.

## Acceptance criteria

- The 404 code is `payment_not_found` with message `Payment was not found`.
- The 409 code is `payment_conflict` with message `Payment conflicts with the current state`.
- Responses reveal neither tracebacks nor SQL details.

## Commands

```powershell
uv run pytest modules/02_python_backend/04_config_errors_logging/exercises/error_mapping -q -rx
```

## Hints

- FastAPI registers exception handlers on the application object.
- Build one small JSON response helper only if it removes duplication.
- Prefer an explicit fallback to a random ID so tests and incident reports remain traceable.
