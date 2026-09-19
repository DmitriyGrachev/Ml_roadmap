# 01 — FastAPI application and routers

## Goal

Create a small API with an application factory, router, predictable status codes, and a health endpoint.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| `@RestController` maps requests. | `APIRouter` groups path operations. |
| `@RequestMapping` selects a route. | Decorators such as `@router.get` declare a path operation. |

**Non-equivalence:** a router is not a controller class; its handlers can remain plain functions.

## Python model

`create_app()` composes a fresh `FastAPI` application and includes an `APIRouter`. Keeping construction in a function makes tests independent.

## Key concepts

- application factory
- path operation and response status
- router inclusion
- health endpoint

## Example

See `../examples/support_api/app.py`: it attaches `/health` and ticket routes to one router.

## Exercises

Read the support API tests first, then add a route only when its request and response contract are explicit.

## Self-check

1. Why return a fresh app from a factory?
2. What should `/health` reveal?
3. When is `201 Created` appropriate?
4. What does a router organize?
5. Why are route functions easy to test?

## Done when

You can create two isolated app instances and explain each registered route.
