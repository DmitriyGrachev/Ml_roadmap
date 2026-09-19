# 08 — API, service, repository, and integration tests

## Goal

Test each boundary at the smallest useful level and prevent application state or dependency overrides from leaking between tests.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| `MockMvc` exercises MVC routes. | `TestClient` exercises FastAPI routes. |
| Test slices isolate layers. | Small app factories and fakes isolate a route or service. |

**Non-equivalence:** a FastAPI `TestClient` test does not need a Spring application context or annotation-driven test slice.

## Python model

Test services directly, API contracts through a fresh app, and persistence with an isolated database. Use fixtures that yield and clean up their own overrides.

## Key concepts

- TestClient
- deterministic fake service
- dependency override cleanup
- characterization test

## Example

The support API test makes two apps and proves that a ticket created in one is absent from the other.

## Exercises

The API-test-review exercise characterizes a coupled fixture, then asks you to make it order-independent.

## Self-check

1. Why build a fresh app per test?
2. What should a route test assert?
3. When is a fake better than a mock?
4. How are overrides cleaned up?
5. What does a characterization test preserve?

## Done when

You can choose the right test level and identify a state leak from test order.
