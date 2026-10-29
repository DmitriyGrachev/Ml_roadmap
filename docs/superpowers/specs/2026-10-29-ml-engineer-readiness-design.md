# ML Engineer readiness: design and acceptance criteria

Date: 2026-10-29 (Europe/Bucharest; research began on 2026-10-28 UTC).
Base: `codex/ai-ml-wave1`, commit `934b34bcaab5c0c241dfa820d807a9bb61e166c6`.
Delivery branch: `codex/ml-engineer-readiness`.

## User goal and authorization

The learner knows Java/Spring backend development and starts Python and AI from the
beginning. The user requested a comparison with current ML Engineer vacancies,
then implementation of the previous audit recommendations on a new branch, using
parallel agents. This is authorization to implement and publish this separate
branch. It is not authorization to merge it or complete the learner's exercises.

## Outcome

A navigable, assessed learning route that develops Python fluency, mathematical
understanding, independent model evaluation and operational delivery. Existing
lessons remain useful prerequisites. New work closes depth and transfer gaps,
rather than pretending that additional topic names demonstrate competence.

The vacancy comparison distinguishes model-building ML Engineer work from
AI/LLM application engineering, and junior requirements from senior/platform
specializations. It records source, date, location, seniority and application
status. A public listing is not confirmation of available headcount or eligibility
to work remotely from Romania.

## Required changes

1. One current learning map with prerequisites, theory, required practice,
   assessment and next steps; current counts come from the catalog. Historical
   plans/reports are explicitly historical. Existing learner progress is preserved.
2. Mandatory independent external tabular and external text projects: provenance,
   feature availability, defensible split, baselines, stronger models, uncertainty,
   error analysis, reproducibility and human defense.
3. Math practice covering MSE/BCE gradients and L2 with finite differences;
   rank/conditioning/Ridge/PCA geometry; decision stump split selection; several
   residual-boosting steps with train/validation comparison.
4. Repeated full training across seeds/splits/sample sizes, distinguished from
   paired bootstrap intervals conditional on fixed predictions.
5. A required real pretrained text comparison (TF-IDF, frozen pretrained encoder,
   adapted encoder). Offline random-model mechanics cannot earn this project's
   completion. LoRA remains an optional extension with an honest base/prompt/LoRA
   comparison and compute limits.
6. Masked mean pooling for the pinned MiniLM route, plus dense retrieval connected
   to a generator and independent retrieval/answer evaluation. Cases cover
   unanswerable, ambiguous, stale and unauthorized evidence. Dev/holdout separation
   prevents tuning to the final evaluation. Existing CLS reports remain labeled.
7. Real HTTP service lifecycle practice: saved model, shared preprocessing,
   container/Linux commands, concurrent requests, timeouts/cancellation, measured
   latency and failures, restart/rollback and monitoring with delayed labels.
8. Python async explanations and exercises for tasks, cancellation, semaphore and
   structured cleanup; explain thread/process boundaries without adding a framework.
9. Build/install a src-layout Python package in a clean environment; use one
   preprocessing implementation in training and serving.
10. Alembic upgrade/backfill/downgrade against a populated database; deterministic
    SQLite author tests and a clearly separated PostgreSQL execution route.
11. Separate untouched-starter maintainer checks from the learner test suite.
    Learners can implement exercises without failing the template-only policy.
12. Review rubrics with weak/strong evidence and a transfer task. New requirements
    have explicit catalog IDs and route checks; old item checks keep their scope.
13. Compact data pipeline practice (SQL, incremental/idempotent processing, quality
    gates, reproducible manifests) and a mapping to one cloud deployment. Spark,
    Airflow, Kubernetes and multiple clouds remain role-specific extensions.
14. Repair the observed Windows UTF-8 CLI failure and the cross-drive relative-path
    test; verify the branch using meaningful runtime tests and CI.

## Global constraints

- Teaching prose is Russian; code identifiers and technical commands may be English.
- Reuse the repository's `exercise_call`, catalog, strict checks, existing labs and
  Document Intelligence service. Do not introduce a parallel learning framework.
- Learner starters retain explicit `NotImplementedError` boundaries. Author demos
  and tests are separate and must not count as learner completion.
- Default tests are offline, deterministic and CPU-capable. Network/model downloads,
  live services and GPU tests require explicit opt-in. Never fabricate run evidence.
- Report technical checks separately from human review and real external experiments.
- New IDs add requirements; old IDs and old check scopes remain compatible.
- Core dependencies remain small; Alembic is an optional `migrations` group. Reuse
  existing `training`, `retrieval`, `tracking` and `finetuning` groups.
- Preserve Windows/PyCharm usability and Linux/WSL delivery instructions. Do not
  make native Windows vLLM or expensive cloud/GPU execution a beginner prerequisite.
- No filled learner reports, changed completion ticks, credentials, downloaded model
  weights, private data or generated databases are committed.
- Work stays on the new branch. Agents own disjoint paths and do not commit or
  modify the shared index; the controller integrates and commits sequentially.

## Acceptance evidence

For every new unit: prerequisites and theory, worked author example, independent
task, behavioral tests or artifact verification, interpretation rubric and transfer
question. Tests demonstrate that incomplete learner work does not receive strict
credit. Mathematical examples include numerical checks and assumptions.

The default suite, maintainer-only gate, Ruff, catalog/link checks and relevant
optional groups pass on supported environments. External data/model and Docker/cloud
execution are reported individually as executed or not run, with reproducible
commands. A whole-branch review checks both implementation and teaching consistency.

## Non-goals

No promise of employment, fabricated assessment of the learner, exhaustive MLOps
platform, mandatory multi-cloud/Spark/Kubernetes course, automatic job applications,
or merge into the source branch.
