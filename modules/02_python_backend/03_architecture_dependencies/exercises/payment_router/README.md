# Exercise — Explicit payment router

## Goal

Compose a payment router from an explicitly supplied service.

## Difficulty

Intermediate.

## Estimated time

35–50 minutes.

## Requirements

- Implement `build_payment_router(service)` in `starter.py`.
- Add `POST /payments` with a 201 response and `GET /payments/{payment_id}`.
- Pass the parsed `PaymentCreate` object to `service.create` exactly once.
- Return a response model that excludes `internal_note`.
- Let `PaymentNotFound` propagate; the error-mapping exercise owns its HTTP response.

## Acceptance criteria

- Two apps created with different services do not share payment state.
- The router does not instantiate its own service or use global mutable state.
- A missing payment remains a `PaymentNotFound` until an exception handler is installed.

## Commands

```powershell
uv run pytest modules/02_python_backend/03_architecture_dependencies/exercises/payment_router -q -rx
```

## Hints

- A router can close over an explicitly supplied service.
- `response_model` is the boundary that filters the public JSON body.
- `Depends` is unnecessary for this first composition step.
