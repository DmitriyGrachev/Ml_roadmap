# Release gates and continuous evaluation

Read the connected [theory](theory.md) for the G-01 manifest and fixed local
comparison before working through this lesson's independent release gate.

## Goal

Compare frozen candidate and baseline releases on the same cases, while distinguishing an
offline release decision from evidence about live behavior after deployment.

## Java mental model

A release gate resembles an acceptance-test policy over a versioned corpus. A missing
record is not a passing test, and a stronger global average can hide a broken user cohort.

## Python model

Track case IDs and complete data/scorer versions. Align results by ID and report support
for each slice before comparing scores. Freeze the policy and holdout before inspecting
candidate results; repeated tuning on that holdout turns it into development data.

## Key concepts

Record code, model, prompt, index, dataset, and scorer identity with each evaluation.
Measure answerability, refusals, evidence quality, and relevant language/task populations;
the required slices belong to the product contract. A minimum sample threshold avoids
treating an empty slice as success but does not establish statistical significance.

Production monitoring must also check input schema changes, stale retrieval sources,
label coverage, and distribution changes. Input drift is a diagnostic signal, not proof
that answer quality declined. Labels may arrive late and only for selected users: join
them to the original request/version and report coverage and delay before drawing
conclusions. Do not silently count unlabeled requests as correct. These distinctions
complement [Google's ML monitoring guidance](https://developers.google.com/machine-learning/crash-course/production-ml-systems/monitoring).

## Example

```powershell
uv run python modules/08_production_ai/02_releases_evaluation/example.py
```

The manifest fingerprints sorted holdout IDs and rejects overlap with development IDs.
It is a miniature provenance example: real case hashes include inputs, expected outputs,
rubrics, and their versions, not only identifiers.

## Exercises

Complete [Compare paired release evaluations](exercises/release_gate/README.md).
Specify which required slices you would add to a live service's release policy.

## Self-check

1. Why must baseline and candidate cover identical cases?
2. Can an overall improvement justify a required-refusal regression?
3. What changes when the scorer changes?
4. Why is input drift not identical to quality drift?
5. How could delayed or selectively observed labels bias online evaluation?

## Done when

You can audit the evaluated population, reject incomplete comparisons, and explain the
additional live measurements required after a candidate passes its offline gate.
