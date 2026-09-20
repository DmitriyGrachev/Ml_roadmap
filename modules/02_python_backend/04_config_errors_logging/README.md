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

Keep settings at the application edge. Subclass `pydantic_settings.BaseSettings` and declare a
`SettingsConfigDict` so the environment prefix and optional `.env` file are explicit. Instantiate
settings during application composition rather than at import time; tests can then isolate the
environment. Map known domain exceptions to stable `code` and `message` fields, and leave unknown
errors to observability tooling.

Structured logging means the event name stays stable while context is stored as record fields. With
the standard library, `logger.info("support_ticket_event", extra={...})` keeps `ticket_id` and
`event` searchable without interpolating request bodies, credentials, or account data into text.

## Key concepts

- typed settings
- `BaseSettings` and `SettingsConfigDict`
- exception handler
- stable error code
- structured log event names and safe context fields

## Example

The runnable support example separates both concerns:

- [`config.py`](../examples/support_api/config.py) binds `SUPPORT_APP_NAME` and
  `SUPPORT_LOG_LEVEL` into typed settings; `create_app(settings=...)` receives that object at the
  composition boundary instead of constructing global settings during import.
- [`observability.py`](../examples/support_api/observability.py) emits a stable event with a ticket
  identifier as structured context.

Their tests change the environment, inspect the resulting typed values, and inspect the actual
`LogRecord`. Separately, `TicketNotFound` becomes a 404 JSON body with `ticket_not_found`; it never
exposes a traceback or storage details.

## Exercises

The [error-mapping exercise](exercises/error_mapping/README.md) adds request IDs and verifies conflict
and missing-resource responses.

## Self-check

1. Which data must never enter payment logs?
2. Why use stable error codes?
3. Where do environment variables become typed settings?
4. Which exceptions deserve an HTTP mapping?
5. Why avoid SQL details in responses?
6. Why instantiate settings at the composition boundary instead of module import?
7. Which log fields are useful for correlation without exposing request data?

## Done when

You can load prefixed environment settings, inspect structured context on a log record, and
distinguish actionable client errors from unexpected server failures.
