# AI Engineer Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub-ready, immediately usable Python-to-AI learning repository for an experienced Java/Spring engineer, with Modules 01–03, testable student exercises, and the progressive Banking AI Lab.

**Architecture:** One Python 3.12+ project uses a shared `uv` environment and a small `roadmap_tools` package for catalog and exercise-test behavior. Curriculum content is isolated by module, while the Banking AI Lab supplies a single domain thread across Python, backend, and data work. Implementation runs in dependency-ordered waves so independent curriculum modules can be built and reviewed in parallel.

**Tech Stack:** Python 3.12+, uv, pytest, pytest-asyncio, Ruff, mypy, FastAPI, Pydantic, Pydantic Settings, SQLAlchemy 2.x, psycopg, HTTPX, NumPy, Pandas, JupyterLab, nbformat

**Spec:** `docs/superpowers/specs/2026-09-19-ai-engineer-roadmap-design.md`

## Global Constraints

- The physical repository root is `C:\ProjectsDirectory\AIML\_road`; the published project name is `ai-engineer-roadmap`.
- Python 3.12 is the minimum supported version and `.python-version` contains `3.12`.
- Use one root `pyproject.toml` and one committed `uv.lock`; do not introduce Poetry, Conda, Pipenv, Hatch, or a second Python environment.
- Student starter boundaries raise `NotImplementedError`; no solution file or solved implementation is committed.
- Examples must differ materially from exercise algorithms and use transaction, payment, banking, API, document, support-ticket, or LLM-style domains.
- The untouched repository health command `uv run pytest` exits zero while visibly reporting expected-incomplete student tests.
- Unexpected exceptions, import errors, syntax errors, and incorrect student results fail normally.
- `scripts/learn.py` reads tracked metadata and never modifies `progress.md` or another tracked file.
- Module 01 lessons run without Docker; PostgreSQL and Docker are opt-in and introduced only in backend stages.
- All financial data is deterministic synthetic data; no real customer or account data is present.
- Documentation is Windows 11 and PyCharm first, while commands remain portable where practical.

## Review Focus

- A starter function raises `NotImplementedError`: its test is expected-incomplete, but an unrelated `ValueError` remains a failure; Foundation Task 1 pins both paths.
- A curriculum identifier is misspelled or points outside the repository: the CLI exits 2, suggests close identifiers, and never executes an arbitrary path; Foundation Task 2 pins this behavior.
- Currency amounts contain more than two decimal places or invalid text: Banking Task 2 rejects the row with a row-numbered validation error instead of rounding silently.
- FastAPI receives invalid or naive timestamps: Backend Task 2 and Banking Task 3 pin 422 responses and timezone-aware serialization.
- Fraud labels are extremely imbalanced or contain only one class: Data Task 2 pins deterministic metric behavior and explains when ROC-AUC or PR-AUC is undefined.

---

## Execution map

The detailed subplans are part of this plan and carry the same global constraints:

1. [Foundation and learning tooling](2026-09-19-foundation-and-tooling.md)
2. [Module 01 — Python core](2026-09-19-python-core.md)
3. [Module 02 — Python backend](2026-09-19-python-backend.md)
4. [Module 03 — Data foundations](2026-09-19-data-foundations.md)
5. [Banking AI Lab](2026-09-19-banking-ai-lab.md)
6. [Integration and delivery](2026-09-19-integration-and-delivery.md)

### Wave 1: Foundation

- [ ] Execute every task in `2026-09-19-foundation-and-tooling.md`.
- [ ] Run `uv run pytest tests/tooling -q`, `uv run ruff check src scripts tests/tooling`, and `uv run mypy src scripts`.
- [ ] Review the foundation interfaces used by all later work: `exercise_call`, `Catalog`, `CatalogItem`, and `scripts/learn.py`.

### Wave 2: Independent curriculum modules

After Wave 1 passes, execute these three plans in parallel with exclusive file ownership:

- [ ] Module 01 worker owns `modules/01_python_core/**` and its entries in `curriculum.toml`.
- [ ] Module 02 worker owns `modules/02_python_backend/**` and its entries in `curriculum.toml`.
- [ ] Module 03 worker owns `modules/03_data_foundations/**` and its entries in `curriculum.toml`.
- [ ] Each worker runs the scoped pytest, Ruff, and mypy commands in its subplan before review.
- [ ] A reviewer checks each module against the spec before Wave 3 begins.

### Wave 3: Progressive project

- [ ] Execute every task in `2026-09-19-banking-ai-lab.md` after the three module interfaces and teaching conventions are stable.
- [ ] Run the project's unit/API tests without PostgreSQL and confirm PostgreSQL tests produce actionable skips.
- [ ] Review the project for accidental solutions to lesson exercises and for consistency with the module terminology.

### Wave 4: Repository integration

- [ ] Execute every task in `2026-09-19-integration-and-delivery.md`.
- [ ] Run the full verification matrix from a fresh `uv sync --all-groups` state.
- [ ] Request a whole-repository review against the design spec and resolve all Critical and Important findings.

## Final interface contract

The completed repository exposes these user-facing commands:

```powershell
uv sync --all-groups
uv run python scripts/learn.py validate-env
uv run python scripts/learn.py list
uv run python scripts/learn.py status
uv run python scripts/learn.py test python-collections
uv run pytest
uv run pytest modules/01_python_core
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

The first learning entry point is `modules/01_python_core/00_environment/README.md`. The first coding entry point is `modules/01_python_core/02_collections/exercises/detect_duplicates/README.md`.

## Spec coverage matrix

| Spec section | Owning plan and task |
|---|---|
| Purpose, audience, architecture, layout | Foundation Tasks 1–4 and this execution map |
| Learning-unit contract | Foundation Task 1 plus every module exercise task |
| Module 01 and first sprint | Python Core Tasks 1–5 |
| Module 02 | Python Backend Tasks 1–4 |
| Module 03 | Data Foundations Tasks 1–4 |
| Banking AI Lab stages 1–7 | Banking Tasks 2–4 |
| Synthetic datasets | Banking Task 1 |
| Exercise test behavior | Foundation Task 1 and Integration Task 4 |
| Dependency policy | Foundation Task 1 and Integration Task 2 |
| Error handling and learner feedback | Foundation Tasks 2–3 plus module-specific acceptance tests |
| Documentation and PyCharm workflow | Foundation Task 4 and Integration Tasks 1–2 |
| Git hygiene | Foundation Task 1 and Integration Tasks 1 and 5 |
| Verification criteria | Integration Tasks 1–5 |
| Delivery report | Integration Task 5, Step 6 |

Self-review found no uncovered spec section. Each cross-cutting failure mode in Review Focus has an owning test step in a detailed subplan.
