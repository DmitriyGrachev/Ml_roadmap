# 09 — Docker runtime packaging

## Goal

Package a completed API for a reproducible runtime without making Docker part of the inner development loop.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| A layered image packages a Boot application. | A Dockerfile installs locked Python dependencies and starts an ASGI app. |
| Compose can provide local services. | Compose can provide an opt-in local PostgreSQL dependency. |

**Non-equivalence:** a Python container does not produce an executable JAR; the ASGI module is selected at runtime.

## Python model

Use a supported slim Python image, install `uv`, sync from the lock file without development dependencies, and run as a non-root user. Keep the app module configurable rather than hard-coded.

> **Docker is optional:** the module's examples and exercises run without building an image or starting Compose.

## Key concepts

- locked dependencies
- non-root runtime user
- ASGI server command
- local-only PostgreSQL compose service

## Example

The later `Dockerfile.example` documents an application module placeholder and a runtime command; it is not needed to run the support API tests. To use the nested Compose example from the repository root in PowerShell, first run `Copy-Item modules/02_python_backend/09_docker_delivery/compose.example.yaml compose.yaml`, then run `docker compose up -d postgres`. After the PostgreSQL checks, clean up with `docker compose down --volumes` followed by `Remove-Item compose.yaml`.

## Exercises

Связный [практикум упаковки готового CPU API](container_practice.md): image/container,
ports/mounts → явный build → HTTP → restart/reload. Материал подготовлен;
реальный container runtime в текущей среде **NOT_RUN**.

Review the [Dockerfile example](Dockerfile.example) and [Compose example](compose.example.yaml) after
the persistence exercises, and never place credentials in an image or committed Compose file.

## Self-check

1. Why sync without development dependencies?
2. Why run as a non-root user?
3. What selects the ASGI application?
4. Which service is local-learning only?
5. Why keep secrets outside an image?

## Done when

You can explain how the image stays reproducible and why Docker remains optional for this module.
