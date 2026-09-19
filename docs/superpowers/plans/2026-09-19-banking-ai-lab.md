# Banking AI Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a seven-stage synthetic banking project that grows from CSV validation into analytics, Pandas, FastAPI, PostgreSQL, integration tests, and exploratory analysis without solving student-owned features.

**Architecture:** Complete infrastructure supplies deterministic data, domain contracts, application construction, fixtures, and health checks. Each stage exposes one typed student boundary guarded by acceptance tests through `exercise_call`. The package lives entirely under `projects/banking_ai_lab` and uses explicit composition between API, service, analytics, and persistence concerns.

**Tech Stack:** Python 3.12+, Pydantic 2, FastAPI, SQLAlchemy 2.x, psycopg 3, Pandas, NumPy, pytest, HTTPX, Jupyter

**Spec:** `docs/superpowers/specs/2026-09-19-ai-engineer-roadmap-design.md`

## Global Constraints

- Use the global constraints and Review Focus in `2026-09-19-ai-engineer-roadmap-implementation.md`.
- Synthetic records contain no names, emails, account numbers, card numbers, or identifiers derived from real data.
- Domain amounts use `Decimal`; Pandas/NumPy views may use floating point only when the lesson explains the boundary.
- Domain timestamps are timezone-aware UTC. CSV serialization uses ISO 8601 with an explicit offset.
- Infrastructure may be complete; every acceptance-test target named in a stage README remains an unimplemented student boundary.

## Review Focus

- CSV row errors include the one-based data row, field name, and safe message without aborting collection of unrelated valid rows.
- Duplicate transaction IDs and byte-for-byte duplicate rows are reported deterministically.
- API pagination rejects negative offsets and non-positive/excessive limits.
- Persistence handles duplicate IDs atomically and does not leave a failed session unusable.
- Dataset regeneration is byte-for-byte deterministic across two clean temporary directories.

---

### Task 1: Deterministic synthetic transaction datasets

**Files:**
- Create: `datasets/README.md`
- Create: `datasets/transactions.csv`
- Create: `datasets/transactions_dirty.csv`
- Create: `scripts/generate_transactions.py`
- Create: `tests/datasets/test_transaction_generation.py`

**Interfaces:**
- Produces `generate_transactions(*, seed: int, count: int) -> list[GeneratedTransaction]`.
- Produces `write_datasets(output_dir: Path, *, seed: int = 20260919, count: int = 1000) -> tuple[Path, Path]`.
- Produces columns `id,user_id,amount,currency,merchant,category,timestamp,status,is_fraud` in that exact order.

- [ ] **Step 1: Write generator tests**

Generate into two temporary directories and assert equal bytes. Pin exact headers, 1,000 clean rows, unique clean IDs, parseable positive two-decimal amounts, UTC timestamps, supported currencies/statuses, at least five merchants/categories, fraud prevalence between 0.05% and 1%, and no forbidden personal-data column names. Pin dirty data containing duplicate IDs, invalid amount, invalid timestamp, unknown status, and a missing optional category.

- [ ] **Step 2: Run tests and confirm the missing generator**

Run: `uv run pytest tests/datasets/test_transaction_generation.py -q`

Expected: import or file-not-found failure.

- [ ] **Step 3: Implement deterministic generation**

Use `random.Random(seed)`, UUID5 derived solely from a synthetic row index and seed, fixed merchant/category/provider vocabularies, weighted statuses, and a rare fraud probability that is higher for selected synthetic risk conditions. Quantize amounts through `Decimal` to two places before CSV serialization. Sort by timestamp and ID before writing with `newline=""` and UTF-8.

- [ ] **Step 4: Generate checked-in files and prove reproducibility**

Run: `uv run python scripts/generate_transactions.py --output datasets --seed 20260919 --count 1000`

Run: `uv run pytest tests/datasets/test_transaction_generation.py -q`

Expected: all generator tests pass.

- [ ] **Step 5: Commit**

Commit generator, docs, tests, and CSVs with message `feat: add synthetic transaction datasets`.

### Task 2: Stages 1–3 — domain, CSV import, reports, and Pandas

**Files:**
- Create: `projects/banking_ai_lab/README.md`
- Create: `projects/banking_ai_lab/banking_ai_lab/__init__.py`
- Create: `projects/banking_ai_lab/banking_ai_lab/domain.py`
- Create: `projects/banking_ai_lab/banking_ai_lab/importer.py`
- Create: `projects/banking_ai_lab/banking_ai_lab/analytics.py`
- Create: `projects/banking_ai_lab/banking_ai_lab/dataframe.py`
- Create: `projects/banking_ai_lab/stages/01_csv_validation/README.md`
- Create: `projects/banking_ai_lab/stages/02_json_reports/README.md`
- Create: `projects/banking_ai_lab/stages/03_pandas_analysis/README.md`
- Create: `projects/banking_ai_lab/tests/conftest.py`
- Create: `projects/banking_ai_lab/tests/test_importer.py`
- Create: `projects/banking_ai_lab/tests/test_analytics.py`
- Create: `projects/banking_ai_lab/tests/test_dataframe.py`

**Interfaces:**
- Produces complete frozen Pydantic `Transaction` with ID, user ID, positive two-decimal Decimal amount, supported currency, merchant, optional category, aware timestamp, status, and boolean fraud label.
- Produces complete frozen `ImportIssue(row_number: int, field: str, message: str)` and `ImportResult(transactions: tuple[Transaction, ...], issues: tuple[ImportIssue, ...])`.
- Produces student boundaries:

```python
def import_transactions(path: Path) -> ImportResult: ...
def build_report(transactions: Iterable[Transaction]) -> TransactionReport: ...
def write_report_json(report: TransactionReport, path: Path) -> None: ...
def transaction_frame(transactions: Iterable[Transaction]) -> pd.DataFrame: ...
def daily_currency_summary(frame: pd.DataFrame) -> pd.DataFrame: ...
```

- [ ] **Step 1: Write complete domain-model tests**

Pin field validation, decimal scale, allowed values, optional category, UTC normalization, naive timestamp rejection, immutability, and safe representation. These are infrastructure tests and pass once the complete model is implemented.

- [ ] **Step 2: Write Stage 1 student tests**

Through `exercise_call`, pin clean import, generator input path, empty file, missing headers, row-level issue collection, duplicate IDs, two-decimal rejection rather than rounding, and a nonexistent path raising `FileNotFoundError`. Tests assert safe error messages do not include a complete CSV row.

- [ ] **Step 3: Write Stage 2 student tests**

Pin counts and totals by currency/status, deterministic top merchants, generator input, empty input, JSON decimal/string and timestamp serialization, UTF-8, parent-directory absence, and atomic behavior that leaves an existing target unchanged if serialization fails.

- [ ] **Step 4: Write Stage 3 student tests**

Pin exact DataFrame columns/dtypes, UTC datetime dtype, category handling, input generator support, empty input schema, daily/currency named aggregations, deterministic sorting, and input-frame immutability.

- [ ] **Step 5: Implement infrastructure and starter boundaries**

Complete domain and report dataclasses because they define contracts, not student algorithms. Each student function includes exact docstrings and raises `NotImplementedError`. Stage READMEs explain which earlier lesson applies, the editable file, acceptance criteria, exact command, 30–90 minute estimate, optional hints, and completion checklist.

- [ ] **Step 6: Run Stages 1–3 gates and commit**

Run: `uv run pytest projects/banking_ai_lab/tests/test_importer.py projects/banking_ai_lab/tests/test_analytics.py projects/banking_ai_lab/tests/test_dataframe.py -q -rx`

Run: `uv run ruff check projects/banking_ai_lab`

Run: `uv run mypy projects/banking_ai_lab`

Expected: infrastructure assertions pass and student boundary assertions are expected-incomplete.

Commit with message `feat: add Banking AI Lab data stages`.

### Task 3: Stages 4–6 — FastAPI, persistence, and integration testing

**Files:**
- Create: `projects/banking_ai_lab/.env.example`
- Create: `projects/banking_ai_lab/banking_ai_lab/config.py`
- Create: `projects/banking_ai_lab/banking_ai_lab/service.py`
- Create: `projects/banking_ai_lab/banking_ai_lab/api.py`
- Create: `projects/banking_ai_lab/banking_ai_lab/app.py`
- Create: `projects/banking_ai_lab/banking_ai_lab/persistence.py`
- Create: `projects/banking_ai_lab/stages/04_fastapi/README.md`
- Create: `projects/banking_ai_lab/stages/05_postgresql/README.md`
- Create: `projects/banking_ai_lab/stages/06_testing/README.md`
- Create: `projects/banking_ai_lab/tests/test_api.py`
- Create: `projects/banking_ai_lab/tests/test_persistence.py`
- Create: `projects/banking_ai_lab/tests/test_postgres_integration.py`
- Create: `projects/banking_ai_lab/Dockerfile`
- Create: `projects/banking_ai_lab/compose.yaml`

**Interfaces:**
- Produces complete `Settings` reading `BANKING_DATABASE_URL`, log level, and API prefix with safe defaults for local SQLite smoke tests.
- Produces complete `create_app(service: TransactionService | None = None) -> FastAPI` with `GET /health` working before student tasks.
- Produces student boundaries `create_transaction`, `get_transaction`, and `list_transactions` on `TransactionService` and `SqlAlchemyTransactionRepository`.
- Produces API contracts for `POST /transactions`, `GET /transactions/{id}`, `GET /transactions`, and `GET /reports/summary`.

- [ ] **Step 1: Write application-factory and health tests**

Assert title/version metadata, `/health` response, independent application instances, dependency override cleanup, and absence of database connection during app construction. These infrastructure tests pass in the starter repository.

- [ ] **Step 2: Write student API acceptance tests**

Through propagated `NotImplementedError` and `exercise_call`, pin create 201, duplicate 409, get 200/404, validation 422 for amount/currency/timestamp, bounded pagination, stable ordering, report schema, and absence of internal exception details. Use deterministic fake repositories.

- [ ] **Step 3: Write SQLite persistence tests**

Pin insert/get/list, duplicate rollback, pagination, user/status filters, decimal and UTC round trip, unknown ID, session cleanup, and recovery after an integrity error. No Docker is involved.

- [ ] **Step 4: Write opt-in PostgreSQL integration tests**

Read `ROADMAP_POSTGRES_URL`; otherwise skip with `cd projects/banking_ai_lab; docker compose up -d postgres`. Use transaction rollback or unique table names, wait through a bounded connection-retry fixture, and pin PostgreSQL numeric/timestamptz semantics plus the API-to-database round trip.

- [ ] **Step 5: Add configuration, starter composition, and containers**

Implement health and exception infrastructure completely. Keep transaction business boundaries unimplemented. The Dockerfile installs the root lock reproducibly, uses a non-root runtime user, copies only required files, and starts uvicorn with `--app-dir projects/banking_ai_lab`. Compose defines PostgreSQL healthcheck, named volume, application dependency on a healthy database, and environment interpolation matching `.env.example`; no real secret is committed.

- [ ] **Step 6: Run Stages 4–6 gates and commit**

Run: `uv run pytest projects/banking_ai_lab/tests/test_api.py projects/banking_ai_lab/tests/test_persistence.py -q -rx`

Run: `uv run pytest -m postgres projects/banking_ai_lab/tests/test_postgres_integration.py -q -rs`

Run: `uv run ruff check projects/banking_ai_lab`

Run: `uv run mypy projects/banking_ai_lab`

Expected without PostgreSQL: working health tests, expected-incomplete feature tests, and actionable PostgreSQL skips.

Commit with message `feat: add Banking AI Lab API and persistence stages`.

### Task 4: Stage 7 exploratory notebook and project contracts

**Files:**
- Create: `projects/banking_ai_lab/notebooks/transaction_eda.ipynb`
- Create: `projects/banking_ai_lab/stages/07_exploratory_analysis/README.md`
- Create: `projects/banking_ai_lab/tests/test_project_contracts.py`
- Create: `projects/banking_ai_lab/tests/test_notebook.py`

**Interfaces:**
- Consumes: `datasets/transactions.csv` and the Stage 3 DataFrame schema.
- Produces a notebook with completed load/inspection cells and unfinished student analysis cells tagged `exercise`.

- [ ] **Step 1: Write project structure tests**

Assert seven numbered stage READMEs, their prerequisite links and commands, the exact transaction fields, catalog project entry, `.env.example` keys, Docker healthcheck, and a root project README progression table.

- [ ] **Step 2: Write notebook contract tests**

Parse with nbformat; assert Python 3 metadata, repository-relative data lookup, Colab fallback note, deterministic seed, at least four exercise-tagged cells, no absolute paths, no credential text, and no stored output over 20 KB.

- [ ] **Step 3: Create the EDA notebook**

Completed cells load and inspect the synthetic CSV, parse dtypes, and display safe aggregate counts. Student cells ask for missing-value analysis, duplicate analysis, amount distributions, merchant/category aggregations, temporal patterns, and fraud-class metrics. Each unfinished cell raises `NotImplementedError("Complete this project stage")`.

- [ ] **Step 4: Run the complete project gate**

Run: `uv run pytest projects/banking_ai_lab -q -rx`

Run: `uv run ruff check projects/banking_ai_lab scripts/generate_transactions.py tests/datasets`

Run: `uv run ruff format --check projects/banking_ai_lab scripts/generate_transactions.py tests/datasets`

Run: `uv run mypy projects/banking_ai_lab scripts/generate_transactions.py`

Expected: infrastructure and contract tests pass, student features are expected-incomplete, and database integration is skipped only when not configured.

- [ ] **Step 5: Commit**

Commit with message `feat: complete progressive Banking AI Lab`.
