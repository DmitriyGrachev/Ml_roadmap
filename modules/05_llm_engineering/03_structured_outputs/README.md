# Structured outputs

## Goal

Accept model output only after explicit structural and application-specific checks, while
recognizing that validated structure alone cannot establish truth.

## Java mental model

Deserializing into a DTO and passing bean validation does not prove the DTO corresponds to
the source document. Treat generated JSON like data received from an untrusted integration.

## Python model

Use `BaseModel.model_validate_json` for the local output boundary, with strict types and
`extra="forbid"`. [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
rejects coercions such as a string into an integer. JSON has no native datetime type, so
strict JSON validation still accepts appropriately formatted datetime strings; strict Python
object validation has different rules.

## Key concepts

Separate three questions: is the JSON parseable, does it satisfy the schema, and does it
satisfy domain/evidence rules? Use ranges and enums for structure; use explicit application
checks or [Pydantic validators](https://docs.pydantic.dev/latest/concepts/validators/) for
relationships such as end time after start time. Reject unknown fields using the model's
[extra configuration](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra).

Provider-constrained generation may improve conformance, but adapters must still handle
refusals, truncation, and transport errors. Do not strip arbitrary prose or code fences until
it happens to parse: choose an explicit rejection or repair policy. A repair is another
bounded generation step, with its own cost and evaluation; it is not a trusted correction.

A verbatim evidence quote provides traceability. Even a genuine quote can be irrelevant or
contradict the answer, so source presence is weaker than entailment or factual accuracy.
Human review or a task-specific evaluator may be needed for consequential claims.

## Example

```powershell
uv run python modules/05_llm_engineering/03_structured_outputs/example.py
```

The catalog model accepts a mineral label. It also accepts the false claim that granite is
a plant because the category belongs to the enum. That deliberate counterexample is the
distinction this lesson asks you to preserve.

## Exercises

Implement the Medium [Museum event contract](exercises/event_contract/README.md): strict
JSON parsing, capacity bounds, timezone-aware chronology, allowed venues, and source evidence.

## Self-check

1. Why can `"40"` be rejected while an ISO datetime string is accepted?
2. What does an unexpected `command` field tell your application to do?
3. Why does finding a quote in the source not prove every extracted field?

## Done when

Your event boundary distinguishes schema failures from domain failures and you can explain
the remaining factual-correctness gap without claiming that the tests measure a real model.
