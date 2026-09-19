# 03 — Dependencies and service boundaries

## Goal

Compose a router, service, and external boundary without turning Python modules into a Spring imitation.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| Constructor injection supplies a service. | A constructor or factory argument supplies a service. |
| A bean interface abstracts an integration. | A `Protocol` can describe an external boundary. |

**Non-equivalence:** `Depends` resolves request dependencies; it is not a replacement for every constructor or a global IoC container.

## Python model

Pass a `TicketService` to `create_app` explicitly. Use `Depends` for request-scoped wiring after the simple composition is visible.

## Key concepts

- explicit constructor composition
- small service objects
- repository protocols at external boundaries
- dependency overrides in tests

## Example

The support API closes over one service instance created by `create_app`, so each app owns its own tickets.

## Exercises

The payment-router exercise receives its service explicitly and adds request-scoped wiring only as an extension.

## Self-check

1. What boundary merits a `Protocol`?
2. Why pass a service to an app factory?
3. When is `Depends` useful?
4. Why reset dependency overrides?
5. What makes an abstraction unnecessary?

## Done when

You can swap a service in a test without a framework-wide container.
