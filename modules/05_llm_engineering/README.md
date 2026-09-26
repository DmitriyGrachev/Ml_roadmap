# Module 05 — LLM Engineering

## Goal

Build the application layer around a language model: explicit requests, validated outputs,
bounded context, measured quality, and permission-controlled tools. Complete Modules 01–03
first; Module 04 provides useful evaluation background but no model training is needed here.

## Java mental model

Treat a model provider like an unreliable remote service behind an interface. A successful
HTTP response is not a business-valid result. Your application still owns DTO validation,
authorization, deadlines, observability, and release criteria.

## Python model

Use `Protocol`, frozen dataclasses, Pydantic 2 models, injected counters and clocks, and
`Decimal` rates. Every example and test runs locally on Python 3.12 with existing repository
dependencies. There are no API keys, model downloads, provider SDKs, or network calls.

## Key concepts

The sequence moves from a provider boundary to a measurable, constrained feature. Fake
responses validate application contracts; they do **not** establish model quality, resistance
to prompt injection, real token usage, or production latency. Retrieval pipelines and agent
orchestration are reserved for later modules.

| Lesson | Practical outcome | Medium practice |
| --- | --- | --- |
| [01 — Interfaces](01_llm_interfaces/README.md) | Swap a deterministic fake behind a typed provider boundary | Apply the interface in lesson 06 |
| [02 — Prompt contracts](02_prompt_contracts/README.md) | Keep task instructions separate from quoted reference data | [Library reference messages](02_prompt_contracts/exercises/prompt_messages/README.md) |
| [03 — Structured outputs](03_structured_outputs/README.md) | Separate schema checks from semantic and evidence checks | [Museum event contract](03_structured_outputs/exercises/event_contract/README.md) |
| [04 — Context and cost](04_context_and_cost/README.md) | Reserve output capacity and compute supplied-rate estimates | [Nature-guide context budget](04_context_and_cost/exercises/context_budget/README.md) |
| [05 — Evaluation](05_evaluation/README.md) | Evaluate answer and refusal slices alongside latency and cost | [Library answer evaluation](05_evaluation/exercises/answer_evaluation/README.md) |
| [06 — Reliability and tools](06_reliability_and_tools/README.md) | Bound retries and validate permission before a tool read | [Bounded provider retries](06_reliability_and_tools/exercises/bounded_retry/README.md) |

## Example

From the repository root:

```powershell
uv run python modules/05_llm_engineering/01_llm_interfaces/example.py
uv run pytest modules/05_llm_engineering
uv run mypy -p modules.05_llm_engineering
```

Each of the six lesson directories contains an independently runnable `example.py`.

## Exercises

Implement the eight Medium starters across the lesson table and additional practice.
Their neutral themes use libraries,
museums, and nature guides. Read the precise input/error contract before implementing;
tests contain expected outcomes and edge cases. `roadmap_tools.exercise_call` marks only
`NotImplementedError` as expected incomplete. Leave tests intact, implement the boundary,
then require its tests to pass with **zero xfails**. Examples teach adjacent mechanics and
are not copies of exercise answers.

Additional practice after the related lessons:

| Lesson connection | New practice |
| --- | --- |
| Context and cost | [Priority-aware library context packing](exercises/context_packing/README.md) |
| Reliability | [Versioned response cache with expiry](exercises/response_cache/README.md) |
| Provider boundary and reliability | [Assemble a museum answer stream](exercises/stream_assembly/README.md) |

## Self-check

1. Which failures can a fake prove your application handles?
2. Why can valid JSON describe a false fact?
3. Who grants permission for a tool action?
4. Why do output reservations, retries, and message framing affect budgets?
5. How would a held-out refusal slice change your release decision?

## Done when

All six examples run, all eight implemented exercise suites pass without xfails, and you
can explain every failure policy. For optional live integration later, implement an adapter
for the lesson 01 interface using the chosen provider's current documentation; configure
credentials outside code, map errors and termination reasons, set timeouts, and measure
real usage and held-out quality. A fake passing locally is not a live deployment sign-off.
