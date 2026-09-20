# 04 — Settings, errors, and structured logs

## Goal

Load configuration safely, map expected domain errors to stable HTTP payloads, and log useful context without secrets.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| `@ConfigurationProperties` binds settings. | `pydantic-settings` validates environment-backed settings. |
| `@ControllerAdvice` handles shared errors. | An app exception handler creates an HTTP response. |

**Non-equivalence:** exception handlers are registered functions, not an advice class discovered by component scanning.

## Python model

Keep settings at the application edge. Map known domain exceptions to stable `code` and `message` fields, and leave unknown errors to observability tooling.

## Key concepts

- typed settings
- exception handler
- stable error code
- structured log fields

## Example

`TicketNotFound` becomes a 404 JSON body with `ticket_not_found`; it never exposes a traceback or storage details.

## Exercises

The [error-mapping exercise](exercises/error_mapping/README.md) adds request IDs and verifies conflict
and missing-resource responses.

## Self-check

1. Which data must never enter payment logs?
2. Why use stable error codes?
3. Where do environment variables become typed settings?
4. Which exceptions deserve an HTTP mapping?
5. Why avoid SQL details in responses?

## Done when

You can distinguish actionable client errors from unexpected server failures.
