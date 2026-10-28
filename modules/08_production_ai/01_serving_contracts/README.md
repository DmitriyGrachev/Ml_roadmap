# Serving contracts and lifecycle

Start with the connected [theory](theory.md); this lesson's museum label example
illustrates lifecycle mechanics alongside the G-01 teacher scenario.

## Goal

Define the request, response, version, and lifecycle contract for a museum-label service.
A running process, an available dependency, and a useful model answer are different facts.

## Java mental model

FastAPI lifespan plays a resource-ownership role similar to application startup/cleanup.
An API schema is a compatibility promise; loading a newer prompt does not waive it.

## Python model

Construct the app through a factory, validate inputs with Pydantic, and acquire shared
resources inside an async lifespan context. The example injects a lifecycle record and
uses an in-process client. It has no model, remote service, or public listener.
See [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/) for startup and cleanup.

## Key concepts

Liveness asks whether the process can make progress; readiness asks whether this instance
should receive new work. Keep dependency failures out of a simplistic restart loop.
During shutdown, mark the instance unready, stop admitting work, drain bounded in-flight
requests, then close resources. The toy example checks admission and cleanup only; actual
server/load-balancer drain behavior and cancellation require separate integration tests.

Version the response schema, application code, model, prompt, retrieval index, and relevant
configuration together. Maintain backward compatibility or expose a deliberate new API
version. Include an internal release ID in diagnostics without revealing secrets or source
documents. Validate response shape and application semantics; an HTTP 200 can still be wrong.

## Example

```powershell
uv run python modules/08_production_ai/01_serving_contracts/example.py
```

Observe a validated fixture response, readiness changing to 503 while liveness stays 200,
and cleanup on context exit. A drained instance also rejects new label requests.

## Exercises

Trace the startup, request, drain, and cleanup states. Write down which real resources need
owners and close operations. Apply release identity in the next lesson's
[release gate](../02_releases_evaluation/exercises/release_gate/README.md).

## Self-check

1. Why can liveness be healthy while readiness fails?
2. What owns the model or connection pool across requests?
3. How does admission control differ from draining in-flight work?
4. Which version changes might invalidate cached answers?
5. Which behavior does the in-process example leave untested?

## Done when

You can explain request validation and resource ownership, identify the exact serving
release, and distinguish local lifecycle checks from a real graceful-shutdown test.
