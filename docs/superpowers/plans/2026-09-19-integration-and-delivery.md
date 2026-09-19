# Integration and Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate every curriculum workstream, lock dependencies, validate commands and notebooks, prove exercise-state behavior, and prepare the concise PyCharm-first handoff.

**Architecture:** Cross-repository contract tests turn documentation links, catalog paths, data reproducibility, and starter boundaries into verifiable interfaces. The final gate runs from the physical repository root using only commands documented for the learner. Independent review checks requirements after all automated gates pass.

**Tech Stack:** uv, pytest, Ruff, mypy, nbformat, Git, PowerShell-compatible commands

**Spec:** `docs/superpowers/specs/2026-09-19-ai-engineer-roadmap-design.md`

## Global Constraints

- Use the global constraints and Review Focus in `2026-09-19-ai-engineer-roadmap-implementation.md`.
- Do not weaken lint, type, or test configuration to hide a concrete defect; scope exclusions only to notebook JSON and intentional broken/review inputs.
- Do not run Docker or require PostgreSQL for the default gate.
- Do not leave temporary correct/incorrect exercise implementations, generated reports, databases, or notebook outputs in the working tree.
- Do not push, configure a remote, or publish the repository.

## Review Focus

- Fresh setup commands work when the repository path contains spaces.
- Root test output distinguishes expected-incomplete work from passing infrastructure.
- Every catalog item resolves to a README and a test target, including all module and project entries.
- Every README command uses the actual path and package layout after integration.
- Git contains no virtual environment, cache, local database, secret, generated report, or unintended solution.

---

### Task 1: Cross-repository contract suite

**Files:**
- Create: `tests/integration/test_catalog_contracts.py`
- Create: `tests/integration/test_markdown_links.py`
- Create: `tests/integration/test_repository_hygiene.py`
- Modify: `curriculum.toml`
- Modify: `progress.md`

**Interfaces:**
- Consumes all README, exercise, catalog, and progress paths.
- Produces a fast integration suite with no network, Docker, or PostgreSQL requirement.

- [ ] **Step 1: Write catalog completeness tests**

Load the real catalog and assert unique IDs, existing README/test paths, all detailed lesson IDs, all 15 first-sprint task IDs, all six later Module 01 practice IDs, all Module 02/03 exercises, and one project entry. Assert `scripts/learn.py list` order matches roadmap order and `status` has a checklist entry for every lesson.

- [ ] **Step 2: Write Markdown link tests**

Parse relative inline links from tracked Markdown while ignoring external URLs, anchors, code fences, and example placeholders. Resolve each link relative to its document and fail with source file and link text. Pin Windows path separator handling with a temporary fixture.

- [ ] **Step 3: Write hygiene tests**

Inspect `git ls-files` and reject `.env`, `.venv`, IDE metadata, cache artifacts, notebook checkpoints, database files, generated reports, and files named `solution`, `answer`, or `completed`. Inspect student starter ASTs to require at least one reachable `NotImplementedError` in every cataloged coding exercise while allowing complete infrastructure modules.

- [ ] **Step 4: Reconcile metadata**

Update `curriculum.toml` and `progress.md` to match actual implemented paths and exact learning order. Do not remove a lesson merely to make the test pass; add missing metadata or missing curriculum content according to the spec.

- [ ] **Step 5: Run integration contracts and commit**

Run: `uv run pytest tests/integration -q`

Expected: all contract tests pass.

Commit with message `test: add repository integration contracts`.

### Task 2: Lock, format, type, and command validation

**Files:**
- Create or update: `uv.lock`
- Modify only files reported by the commands below for concrete compatibility, formatting, lint, or typing defects.

**Interfaces:**
- Produces a fresh-installable lock and zero-exit default quality commands.

- [ ] **Step 1: Re-resolve and synchronize dependencies**

Run: `uv lock --check`

If the lock is absent or stale, run `uv lock`, then `uv sync --all-groups`. Run `uv lock --check` again and require exit zero.

- [ ] **Step 2: Run formatting without changing notebook exercise cells**

Run: `uv run ruff format . --exclude '*.ipynb'`

Run: `uv run ruff format --check . --exclude '*.ipynb'`

Expected: the check exits zero.

- [ ] **Step 3: Run lint and type gates**

Run: `uv run ruff check .`

Run: `uv run mypy`

Fix reported production, example, starter, and test defects. For intentional broken inputs, use the narrow configured path exclusions already named by their lesson rather than blanket ignores.

- [ ] **Step 4: Validate every public command**

Run the commands below from `C:\ProjectsDirectory\AIML\_road`:

```powershell
uv run python scripts/learn.py validate-env
uv run python scripts/learn.py list
uv run python scripts/learn.py status
uv run python scripts/learn.py test python-collections
uv run pytest modules/01_python_core -q -rx
uv run pytest modules/02_python_backend -q -rx
uv run pytest modules/03_data_foundations -q -rx
uv run pytest projects/banking_ai_lab -q -rx
```

Every command must exit zero in the untouched starter state; outputs must display expected-incomplete cases rather than describe them as passed.

- [ ] **Step 5: Commit**

Commit the lock and compatibility corrections with message `build: lock and validate learning environment`.

### Task 3: Notebook and dataset execution smoke tests

**Files:**
- Create: `tests/integration/test_notebook_execution.py`
- Modify only notebook setup cells that fail against the checked-in dataset.

**Interfaces:**
- Consumes four notebooks and deterministic datasets.
- Produces a smoke harness that executes completed setup/example cells while treating exercise-tagged cells as student-owned.

- [ ] **Step 1: Write safe notebook execution extraction**

Load each notebook with nbformat, copy it in memory, replace cells tagged `exercise` with `pass`, and execute the resulting temporary notebook through the installed Jupyter kernel with repository root as working directory. Set a per-cell timeout of 30 seconds and disable network-dependent cells; the notebooks must not contain any network requirement.

- [ ] **Step 2: Run notebook smoke tests**

Run: `uv run pytest tests/integration/test_notebook_execution.py -q`

Expected: all completed cells execute against `datasets/transactions.csv` with no traceback.

- [ ] **Step 3: Re-run dataset determinism**

Run: `uv run pytest tests/datasets/test_transaction_generation.py -q`

Run the generator into a temporary directory and compare SHA-256 hashes for both CSV files with the checked-in versions. The test owns cleanup; no generated directory remains under the repository.

- [ ] **Step 4: Commit**

Commit the smoke harness and any notebook setup corrections with message `test: verify notebooks and datasets`.

### Task 4: Prove exercise feedback states

**Files:**
- Temporarily modify and restore: `modules/01_python_core/02_collections/exercises/provider_frequency/starter.py`
- No persistent file is created by this task.

**Interfaces:**
- Proves expected-incomplete, incorrect, and correct states for the representative first exercise boundary.

- [ ] **Step 1: Record the untouched state**

Run the provider-frequency test with `-q -rx` and require expected-incomplete status plus exit zero.

- [ ] **Step 2: Apply a deliberately incorrect implementation**

Replace the `NotImplementedError` only with `return {}` using a reversible patch. Run the focused test and require at least one failed assertion plus nonzero exit.

- [ ] **Step 3: Apply a temporary correct implementation**

Replace the incorrect return with a local counting loop that preserves first-seen key order. Run the focused test and require all focused tests passed plus exit zero.

- [ ] **Step 4: Restore the exact starter**

Reverse the temporary patch using an explicit apply patch, rerun the focused test, and require expected-incomplete status plus exit zero. Run `git diff --exit-code` for that starter file to prove no solution remains.

### Task 5: Full verification and independent review

**Files:**
- Modify only files required to resolve verified review findings.

**Interfaces:**
- Produces evidence for every acceptance criterion and a clean reviewable repository state.

- [ ] **Step 1: Run the full default gate**

Run:

```powershell
uv sync --all-groups
uv run pytest -q -rx
uv run ruff check .
uv run ruff format --check . --exclude '*.ipynb'
uv run mypy
git diff --check
git status --short
```

Capture exact pass, expected-incomplete, and skip counts. Any failure blocks completion.

- [ ] **Step 2: Audit the design spec line by line**

Create a private verification checklist from all 16 spec sections. For each requirement, identify the implementing file and test or command. Add missing implementation or verification rather than weakening the spec.

- [ ] **Step 3: Request an independent whole-repository review**

Give the reviewer the design spec, master plan, Git base and head SHAs, and these focus areas: accidental solutions, exercise-test semantics, curriculum coverage, modern library APIs, Windows/PyCharm accuracy, data privacy, and command reproducibility. Resolve every Critical and Important finding; record Minor findings only if genuinely optional.

- [ ] **Step 4: Re-run the full gate after fixes**

Repeat Step 1 on the final tree and require fresh zero-exit output. Do not reuse results from before review fixes.

- [ ] **Step 5: Commit final verified corrections**

Commit only if Step 4 passes, using message `chore: finalize verified learning repository`.

- [ ] **Step 6: Prepare the delivery report**

Report the root path, high-level structure, implemented modules, exact verification counts, PyCharm interpreter path, first setup command `uv sync --all-groups`, first lesson path, first exercise path, student-owned starter boundaries, PostgreSQL skip status, and the neutral technical commit identity used because no user Git identity was configured.
