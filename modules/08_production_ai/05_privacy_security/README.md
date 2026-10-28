# Privacy and operational security

Read the connected [theory](theory.md) for the G-01 event/checkpoint boundary
before the separate redaction and retention exercises.

## Goal

Minimize data crossing service, model, retrieval, and telemetry boundaries while retaining
enough operational evidence to investigate failures.

## Java mental model

Authorization belongs to the application, independently of a model's prose or tool request.
A prompt that asks for permission is not a credential, and a retrieved document is not policy.

## Python model

Pass an application-authenticated principal to an allowlisted operation and check tenant
ownership plus scope before reading. The example receives trusted fixture principals;
it does not implement authentication. Real adapters must validate identity and cannot
accept a caller- or model-invented scope as authority.

## Key concepts

Map where source text, embeddings, prompts, outputs, and logs travel and who can read them.
Apply retrieval access filters before materializing unauthorized content into model context;
enforce tool permissions again at execution. Indirect instructions in documents or tool
results remain untrusted data, even if JSON parsing or citation checks succeed.

Prefer bounded operational metadata over raw prompts, provider headers, or full exceptions.
Keep credentials out of source, telemetry, and model context; inject them through the
deployment's secret facility with limited access and rotation. Define retention/deletion
ownership for logs, caches, and indexes; removing a source document may leave derived copies.
These are engineering controls, not a claim about any particular legal requirement.

An allowlist constrains fields but cannot know whether an allowed value contains personal
information. Hashing a stable identifier also does not automatically make it anonymous.
Review instrumentation and export paths as well as your own logging calls; see
[OpenTelemetry's sensitive-data guidance](https://opentelemetry.io/docs/security/handling-sensitive-data/).

## Example

```powershell
uv run python modules/08_production_ai/05_privacy_security/example.py
```

A museum principal can read its own scoped fixture and is denied cross-tenant access.
No prompts, credentials, real private records, or remote calls are involved.

## Exercises

Complete [Minimize structured event logs](exercises/redact_events/README.md).
Name fields you would avoid collecting and who owns the remaining retention policy.

## Self-check

1. Can a retrieved document grant a tool additional permission?
2. Why must access filtering happen before building model context?
3. What sensitive data can remain inside an allowed field?
4. Where else can a deleted source survive as derived data?
5. Why is an authenticated identity different from an authorized action?

## Done when

You can trace data and authority boundaries, keep a useful minimal event schema, and
state the risks that schema validation or local permission tests cannot prove absent.
