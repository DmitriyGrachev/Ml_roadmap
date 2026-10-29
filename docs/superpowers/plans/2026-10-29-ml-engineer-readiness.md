# ML Engineer readiness implementation plan

Spec: [design and acceptance criteria](../specs/2026-10-29-ml-engineer-readiness-design.md).
Base: `934b34bcaab5c0c241dfa820d807a9bb61e166c6`.

## Global Constraints

- Teaching prose is Russian; code identifiers and technical commands may be English.
- Reuse `exercise_call`, catalog, strict checks and existing labs/service. No second learning framework.
- Learner starters retain `NotImplementedError`. Author demos never count as learner completion.
- Default tests are offline, deterministic and CPU-capable; external/model/live/GPU work is opt-in.
- Technical PASS, human review and actual external experiments are distinct evidence.
- Preserve all old IDs/check scopes and existing learner progress.
- Only the controller edits shared files: `pyproject.toml`, `uv.lock`, `curriculum.toml`,
  `progress.md`, root README, `docs/roadmap.md`, `docs/testing-exercises.md`,
  `docs/learning-rules.md`, `.github`, `src/roadmap_tools`, `tests/integration` and
  `tests/tooling`. Ask the controller to integrate a manifest; do not edit these paths.
- Agents work in `/workspace/scratch/938ce92ed17e/roadmap-implementation` on disjoint
  files. No agent commits, stages, checks out branches or starts subagents.
- Each implementation report lists exact IDs, paths, starter function boundaries,
  test commands/results, dependencies and remaining execution limits.
- Behavioral changes use focused failing tests first; do not add prose-word assertions.
- Do not commit external data/models, runtime reports/databases, secrets or completed student work.

## Task 1: Mathematical depth and training stability

Own only these new directories (and their files):

- `modules/04_machine_learning/exercises/gradient_derivations/` — ID `ml-gradient-derivations`.
- `modules/04_machine_learning/exercises/linear_geometry/` — ID `ml-linear-geometry`.
- `modules/04_machine_learning/exercises/tree_boosting/` — ID `ml-tree-boosting`.
- `modules/03_data_foundations/exercises/training_stability/` — ID `data-training-stability`.

Create README, substantial `theory.md`, runnable author `demo.py`, intentionally
incomplete `starter.py`, and meaningful `test_demo.py`/`test_starter.py` for each.
Teach the exact reduction conventions before deriving batch MSE/BCE w/b gradients
and L2; verify finite differences and library agreement, stable BCE at extreme logits.
Geometry must show rank deficiency, condition number, Ridge and a hand-computable
2x2 PCA covariance example. Trees must enumerate candidate thresholds, weighted Gini
or SSE, and 2–3 residual boosting steps with validation (no test-set selection).
Stability must retrain across permissible seeds/splits and sample sizes, keep a
locked holdout separate, and contrast this variability with paired bootstrap
conditional on fixed predictions. Explain group/time constraints and dependence.
Each unit needs a weak/strong answer, an independent transfer problem and explicit
strict-check commands. Author examples must not solve the identical starter task.
Use existing NumPy/sklearn only. Return catalog manifests and boundary names to root.

## Task 2: Python delivery, async lifecycle and schema migrations

Own these new directories plus the existing `10_asyncio/theory.md` only:

- `modules/01_python_core/exercises/async_lifecycle/` — ID `python-async-lifecycle`.
- `modules/01_python_core/exercises/package_delivery/` — ID `python-package-delivery`.
- `modules/02_python_backend/exercises/schema_migrations/` — ID `backend-schema-migrations`.

Create Russian theory, author demos and independent starter exercises/tests.
Async explains coroutine vs Task, create_task, TaskGroup, Semaphore, CancelledError,
timeout and cleanup on happy path, sibling failure and external cancellation.
Use events/fakes to test bounded work and absence of orphan tasks without fragile
sleep timing. Explain `to_thread`/process use and cancellation limitations.
Packaging includes an actual tiny src-layout example buildable with the existing
uv_build backend, a `python -m` entry, a shared train/serve transform and a script/test
that installs a wheel in a clean temp environment and runs from outside the source
tree. No network during tests. Independent starter transfer uses a distinct transform.
Alembic includes actual migrations and populated SQLite upgrade/backfill/downgrade
tests, data preservation and a transaction/failure discussion; PostgreSQL is an
explicit optional route. Root adds `migrations = ["alembic>=1.16,<2"]` and locks it.
Tests with missing optional dependency skip explicitly; strict exercise credit must
not treat that skip as success. Student work is separate from author migration demo.
Report commands, ownership, dependency and starter boundary names to root.

## Task 3: Independent external ML projects and assessment

Own these new directories only:

- `projects/external_tabular/` — project ID `ml-external-tabular`.
- `projects/document_intelligence_lab/external_model_study/` — project ID `document-external-model-study`.

Design two substantial independent projects, not merely report headings. Include
source selection/provenance/license/hash, schema checks, leakage audit and feature
availability, train/dev/final holdout/group or time split rationale, row-ID manifests,
baselines and stronger alternatives, paired comparison/uncertainty, error slices,
reproducible commands and defense rubric. Provide an executable author walkthrough
with a separate small fixture; require external data and independently authored work
for the submission gate. Machine-check saved predictions/labels/split disjointness,
recomputed metrics and data/artifact hashes where possible. Missing submissions
xfail in default tests and fail strict credit; arbitrary report strings are insufficient.
Use a clear ignored `submission/` convention with README commands; no learner report
is prefilled. Unit-test validators with adversarial metadata, not only happy path.
Use a public low-compute tabular source (e.g. UCI wine quality) with explicit download
outside default tests; never pretend a tiny synthetic fixture measures real quality.
For text, reuse existing `labs/02_huggingface_models` and Document Intelligence
interfaces. Require TF-IDF, a real pretrained frozen encoder, and adapted encoder on
the same locked external split. Explain why random-encoder mechanics cannot satisfy
this requirement. Add optional base/prompt/LoRA comparison (no GPU requirement).
Document small/budgeted CPU commands and optional GPU route. Rubrics include weak,
strong and transfer evidence, and explicitly keep human review outside technical PASS.
No edits to shared catalog or existing lab code. Report a precise integration manifest.

## Task 4: End-to-end RAG and valid pooling

Own `labs/03_real_rag/dense.py` and related pooling tests, plus new
`labs/03_real_rag/end_to_end/` — ID `rag-end-to-end-evaluation` (exercise).
Reuse the pinned MiniLM artifact identity and existing Ollama generator boundary.
Add an explicit masked-mean pooling mode with L2 normalization, padding/empty-mask
behavior and shape validation. Preserve explicit old CLS reports and compatibility.
Connect retrieval to generator in an actual runner. Separate retriever relevance
metrics from answer correctness/support/abstention, split dev vs heldout, and cover
missing, ambiguous, stale and ACL-restricted evidence. Fit/tune only on dev. Tests
with deterministic providers prove wiring and policy; a live command uses the local
model without being called by offline CI. No claim that fake-provider results are
real language quality. Add independent starter/evidence requirement, theory and
rubric. Live evaluation reports must record model identity, corpus/query/prompt hashes,
latency and every case, and may honestly report poor results.
Coordinate any `requires_training` flag with root; old tests/checks keep scope.

## Task 5: Real service lifecycle, data pipelines and cloud bridge

Own new `projects/document_intelligence_lab/production_readiness/` (ID
`production-service-lifecycle`, exercise), new `projects/document_intelligence_lab/data_pipeline/`
(ID `ml-data-pipeline`, exercise), and existing service files only when necessary to
reuse their actual application; report any proposed cross-scope edits first.
Use saved model/shared preprocessing and existing service/lifecycle APIs. Add runnable
real TCP/uvicorn lifecycle harness with bounded concurrent load, timeout/failure
counts, cold/warm latency measurements, restart and A→B→A rollback checks. Include
Docker/Linux/WSL commands and a minimal Dockerfile if none appropriate exists.
Actual Docker runtime may be unavailable; distinguish static build configuration
from measured TCP runs and external cloud evidence. Use local child processes only,
cleanup reliably; optional runtime marker if sockets unsupported, with a required
explicit learner run/artifact gate. Explain delayed labels, input drift vs model
quality, threshold actions and monitoring limitations.
Data pipeline practice must run SQL extraction, incremental/idempotent loading with
duplicate/late/invalid cases, deterministic manifests and replay. Teach Parquet/Arrow
conceptually without a heavy mandatory dependency; map this local contract to ONE
cloud (object store, container runtime, jobs, identity, logs, monitoring, rollback,
cleanup/cost controls), plus optional role-specific orchestration. No paid deployment.
Each unit has Russian theory, author demo, independent starter/test, defense rubric,
and explicit required evidence. Do not replace the existing architecture.

## Task 6: Integration, CI repair and canonical learner route

Controller owns shared files. First record the dated vacancy comparison with source
links and distinguish must-have vs duties/nice-to-have, junior vs senior and geography.
Repair Windows CLI UTF-8 using a regression that forces cp1252 output, and the
cross-drive test fixture without weakening path behavior. Separate maintainer-only
untouched-starter tests using a registered marker/explicit opt-in command while
keeping artifact hygiene in ordinary CI. Add a test proving solved starter work is
not blocked by the learner workflow. Add Linux CI alongside Windows where useful.

Integrate the 12 new IDs with tests, progress (unchecked), exact starter boundaries
and navigation. Add a small `learning_tracks.toml` and CLI `track` / `check-track`
layer over existing catalog checks: ordered prerequisite route, explicit new items,
optional tracks not cumulative prerequisites. Technical route checks must not mark
human review complete, bypass xfails, or hide missing optional dependencies. Preserve
all original ID semantics. Add `inventory` output from catalog for current counts.

Canonical `docs/learning-map.md` connects prerequisites, theory, required work,
assessment and next step; root README and `docs/roadmap.md` link it and remove stale
current counts/statuses. Historical plans and verification reports remain snapshots.
Update learner rules to allow explicit external-data projects while keeping defaults
offline. Add assessment rubric and verification report with exact executed/not-run
evidence. Root locks Alembic dependency and runs catalog/link/lint/default/maintainer
and relevant optional suites. Newfiles must be staged for tracked-file validators.

## Review and delivery

Wave 1: Tasks 1, 2, 3 in parallel with disjoint ownership; controller works Task 6.
Review each scope for spec and quality with a fresh agent. Wave 2: Tasks 4 and 5 in
parallel after interfaces are fixed, then task reviews and integration. One broad
whole-branch review checks all requirements and remaining regressions. Controller
commits serially, pushes only `codex/ml-engineer-readiness`, verifies the remote head
and CI, and opens a draft PR against `codex/ai-ml-wave1` if supported. No merge.
