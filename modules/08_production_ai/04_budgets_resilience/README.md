# Budgets, deadlines and resilience

## Goal

Bound work by time, concurrency, and cost before an expensive provider call starts.
Preserve correctness when requests fail, retry, time out, or are cancelled.

## Java mental model

Use familiar admission control, semaphore, quota, and timeout concepts. Retry wrappers and
circuit breakers address different failure patterns; adding both without shared budgets
can amplify an overloaded dependency.

## Python model

Calculate remaining stage time from one monotonic deadline, then configure it at the actual
I/O boundary. Propagate cancellation and close resources; a numeric timeout calculation
does not interrupt work by itself. The example injects time and never sleeps.

## Key concepts

Reserve a conservative cost envelope before work, settle measured usage afterwards, and
release unused capacity. Failed calls and retries may still incur cost. A shared live quota
needs atomic updates and durable request identity; a local replay cannot provide these.
Unknown remote outcomes require reconciliation before treating a timeout as a free cancellation.

Limit concurrent and queued requests; reject excess work early with a documented response.
Retry only appropriate transient failures within a shared attempt/deadline/cost budget.
A circuit breaker can stop calls after repeated failures, then allow limited probes before
closing; configure its failure classes and recovery policy. See the SRE discussion of
[overload](https://sre.google/sre-book/handling-overload/) and
[shared deadlines](https://sre.google/sre-book/addressing-cascading-failures/).

Cache keys must include tenant/access scope, relevant model/prompt/index versions, and
normalized input where appropriate. Bound retention and size; define freshness and
invalidation. A cheap stale or cross-tenant answer is not a correct optimization.

## Example

```powershell
uv run python modules/08_production_ai/04_budgets_resilience/example.py
```

A later stage receives less remaining time under the same deadline. An exhausted deadline
raises before starting more work. No network cancellation is simulated.

## Exercises

Complete [Track a request budget ledger](exercises/budget_reservation/README.md).
Explain which synchronization and reconciliation work a live implementation would add.

## Self-check

1. Can a timed-out call still consume provider usage?
2. Why must retries share a deadline and cost budget?
3. How does a circuit breaker differ from a concurrency limit?
4. Which release or permission change invalidates a cached answer?
5. Why can two correct local ledgers still overspend a shared account?

## Done when

You can account for reservations and final usage, choose a bounded failure policy, and
separate pure budget calculations from enforced live admission and cancellation.
