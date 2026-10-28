# Rollouts, rollback and incident response

Read the connected [theory](theory.md) for the fixed G-01 candidate comparison
and incident timeline; the rollout algorithm remains independent practice.

## Goal

Limit exposure while evaluating a release, make stop conditions explicit, and prepare a
recovery procedure that works with the current artifacts, data, and dependencies.

## Java mental model

A release changes a composed service, not just a code package. Rolling back an application
binary does not undo a database migration, restore a deleted index, or erase provider costs.

## Python model

Represent rollout policy and observed windows as immutable data. A pure decision function
can recommend hold, promote, or rollback; a separate authorized control plane would enact
that recommendation. The exercise deliberately has no control-plane integration.

## Key concepts

Shadow requests exercise a candidate without returning its result to the user, but still
consume resources and must not duplicate tools or other side effects. Canary traffic returns
candidate results to a limited population. Define cohort assignment, sample coverage,
comparison windows, and stopping rules before exposure. Consecutive-window requirements
reduce oscillation but do not replace uncertainty analysis. See the
[SRE canarying guidance](https://sre.google/workbook/canarying-releases/).

Retain the prior version and verify compatibility with schemas, prompts, indexes, caches,
and tool contracts. Stop increasing exposure when evidence is missing. For incidents,
stabilize user impact, name an incident owner and communication channel, record a timestamped
timeline, and preserve only appropriate diagnostic evidence. A rollback may need a different
mitigation if prior artifacts are unavailable or no longer compatible.

A runbook states symptoms, scope, dashboards, safe mitigations, recovery checks, owners,
and escalation. Practice it in a simulation. After recovery, write a blameless account of
impact, contributing conditions, detection gaps, and owned follow-up actions; see
[SRE postmortem practice](https://sre.google/workbook/postmortem-culture/).

## Example

```powershell
uv run python modules/08_production_ai/06_rollout_incidents/example.py
```

The local preflight shows why an old release that reads schema 1 cannot automatically be
restored after stored data moves to schema 2. It performs no artifact download or deployment.

## Exercises

Complete [Decide a bounded canary rollout](exercises/rollout_decision/README.md), then write
a short runbook for a museum-label latency incident using the lesson's checklist.

## Self-check

1. Why can shadow traffic still have cost or side-effect risks?
2. What evidence justifies promotion when a required cohort has no samples?
3. How do consecutive-window rules prevent oscillating recommendations?
4. What can make a previously working release unsafe to restore?
5. Which recovery checks confirm user impact has actually ended?

## Done when

You can explain every simulated decision, identify a rollback compatibility constraint,
and hand another person a concrete incident runbook. Local success does not execute or
validate a real production rollout.
