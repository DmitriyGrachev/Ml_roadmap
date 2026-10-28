# Module 08 — Production AI

## Goal

Operate an AI-backed feature as a versioned, measurable service with explicit resource,
data-access, and release policies. Six local lessons connect serving contracts to release
evaluation, telemetry, budgets, privacy, and incident response. Eight Medium exercises
use museum and library services, including the existing request-metrics exercise.

Read the connected [Production AI theory](01_serving_contracts/theory.md) after the
[Agents scenario](../07_agents/01_workflows_state/theory.md). The
[offline operations walkthrough](walkthrough.py) reuses its fixed G-01 cases and writes
teacher evidence only to a fresh directory requested with `--output-dir`.

## Prerequisites

Complete the implemented backend and data foundations modules, then
[LLM Engineering](../05_llm_engineering/README.md),
[RAG](../06_rag/README.md), and [Agents](../07_agents/README.md).
Review [FastAPI](../02_python_backend/README.md), immutable records, Decimal, validation,
and offline evaluation. No cloud account, Docker service, API key, model download, or
additional dependency is required for this module.

## Java mental model

The application still needs ordinary service engineering: contracts, resource ownership,
authorization, deadlines, releases, and incident handling. AI adds versioned prompts,
retrieval data, nondeterministic outputs, and often delayed quality labels to that work.

## Python model

Use FastAPI lifespan for local lifecycle examples, frozen dataclasses for policy inputs,
Decimal for accounting, and pure functions for reviewable decisions. Tests control the
inputs and time. Local simulations verify their contracts; they do not certify a service's
live safety, availability, concurrency behavior, statistical power, or deployment readiness.

## Key concepts

| Lesson | Operational question | Medium exercise |
| --- | --- | --- |
| [01 — Serving](01_serving_contracts/README.md) | Which version is serving, and can it accept work? | Trace the local lifecycle |
| [02 — Releases](02_releases_evaluation/README.md) | Does every evaluated slice satisfy the release policy? | [Paired release gate](02_releases_evaluation/exercises/release_gate/README.md) |
| [03 — Observability](03_observability/README.md) | Which user-visible signals and denominators matter? | [Request metrics](exercises/request_metrics/README.md) |
| [04 — Resilience](04_budgets_resilience/README.md) | Can work fit both cost and time budgets? | [Request budget ledger](04_budgets_resilience/exercises/budget_reservation/README.md) |
| [05 — Privacy](05_privacy_security/README.md) | What may cross each data boundary? | [Structured log minimization](05_privacy_security/exercises/redact_events/README.md) |
| [06 — Rollouts](06_rollout_incidents/README.md) | When should exposure change, and how can it be restored? | [Canary decision](06_rollout_incidents/exercises/rollout_decision/README.md) |

## Example

From the repository root:

```powershell
uv run python modules/08_production_ai/01_serving_contracts/example.py
uv run pytest modules/08_production_ai -q -rx
uv run mypy -p modules.08_production_ai
```

Every lesson has a deterministic, independently runnable `example.py` and behavior tests.
The serving example uses an in-process client; no network listener is opened.

## Exercises

Implement the eight Medium boundaries through their focused README commands. Untouched
starters raise `NotImplementedError` and report `xfail`; a finished answer must pass without
xfails. Examples demonstrate adjacent mechanics and do not contain the complete exercise
algorithms. Keep test expectations intact and explain the limitations of each policy.

## Self-check

1. Which artifacts besides a model name identify a release?
2. What does a missing quality label mean for an online metric?
3. Which failures should consume an error or cost budget?
4. What remains private after a telemetry field allowlist is applied?
5. Can the previous release still read the current stored data?

## Done when

You can run six examples, complete eight exercises, and write a small launch/runbook plan
covering owners, measured objectives, quotas, data access, rollout and recovery. Validate
live infrastructure, concurrency, permissions, and real quality separately before operating
a real service. This module makes no deployment changes.

## Additional practice map

These three independent tasks extend the five core exercises above with pure local policies.

| Exercise | Focus | Estimate |
| --- | --- | --- |
| [Check a library artifact manifest](exercises/artifact_manifest/README.md) | Versioned names and SHA-256 of byte snapshots | 40–65 min |
| [Account for a catalog service error budget](exercises/error_budget/README.md) | Complete-window aggregation and no-data policy | 35–60 min |
| [Plan library record retention](exercises/retention_policy/README.md) | UTC cutoffs, legal holds, and deletion candidates | 35–60 min |
