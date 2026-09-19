# Module 02 Python Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach production Python and FastAPI through Spring-aware explanations, runnable non-banking examples, and tested starter exercises that lead into the Banking AI Lab.

**Architecture:** Nine lessons introduce one backend concern at a time. A small working support-ticket example demonstrates framework mechanics without revealing banking-project solutions; exercises use payment contracts and explicit composition. SQLite proves generic persistence behavior, while PostgreSQL checks are opt-in and clearly marked.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic 2, Pydantic Settings, SQLAlchemy 2.x, psycopg 3, HTTPX, pytest, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-09-19-ai-engineer-roadmap-design.md`

## Global Constraints

- Use the global constraints and Review Focus in `2026-09-19-ai-engineer-roadmap-implementation.md`.
- Use current Pydantic 2 and SQLAlchemy 2 typed APIs; do not teach deprecated v1 or legacy query syntax.
- Prefer functions and explicit constructor composition; do not reproduce a Spring container or require a class per layer.
- Unit and API tests run without Docker. PostgreSQL tests require `ROADMAP_POSTGRES_URL` and otherwise skip with an exact startup command.
- All API timestamps are timezone-aware ISO 8601 values and all domain money values are decimal.

## Review Focus

- Validation rejects unknown currency codes, non-positive amounts, and naive timestamps with field-specific 422 details.
- Dependency overrides are reset after every test so test order does not leak state.
- Async code never calls a blocking database or HTTP operation directly on the event loop.
- SQLAlchemy sessions roll back on errors and close on both successful and failing requests.
- Domain exceptions map to stable JSON error codes without exposing stack traces or SQL details.

---

### Task 1: Backend lesson sequence and support-ticket example

**Files:**
- Create: `modules/02_python_backend/README.md`
- Create: `modules/02_python_backend/01_fastapi/README.md`
- Create: `modules/02_python_backend/02_pydantic/README.md`
- Create: `modules/02_python_backend/03_architecture_dependencies/README.md`
- Create: `modules/02_python_backend/04_config_errors_logging/README.md`
- Create: `modules/02_python_backend/05_async_endpoints/README.md`
- Create: `modules/02_python_backend/06_sqlalchemy/README.md`
- Create: `modules/02_python_backend/07_postgresql/README.md`
- Create: `modules/02_python_backend/08_api_integration_testing/README.md`
- Create: `modules/02_python_backend/09_docker_delivery/README.md`
- Create: `modules/02_python_backend/examples/support_api/__init__.py`
- Create: `modules/02_python_backend/examples/support_api/app.py`
- Create: `modules/02_python_backend/examples/support_api/models.py`
- Create: `modules/02_python_backend/examples/support_api/service.py`
- Create: `modules/02_python_backend/examples/support_api/test_app.py`

**Interfaces:**
- Produces: `create_app(service: TicketService | None = None) -> FastAPI`.
- Produces: `TicketCreate`, `TicketResponse`, and in-memory `TicketService` for a non-banking example.
- Produces catalog IDs `backend-fastapi`, `backend-pydantic`, `backend-architecture`, `backend-config-errors`, `backend-async`, `backend-sqlalchemy`, `backend-postgresql`, `backend-testing`, and `backend-docker`.

- [ ] **Step 1: Write support API tests**

Test `GET /health` returning `{"status": "ok"}`, valid ticket creation returning 201 and a generated identifier, blank subject returning 422, missing ticket returning `{"code": "ticket_not_found", "message": "Ticket was not found"}`, and two application instances having independent in-memory state.

- [ ] **Step 2: Run tests and confirm missing application failure**

Run: `uv run pytest modules/02_python_backend/examples/support_api/test_app.py -q`

Expected: import failure for the absent example application.

- [ ] **Step 3: Implement the deliberately small example**

Use an application factory, `APIRouter`, Pydantic request/response models, an explicit service object, and one exception handler. Store tickets in an instance-owned dictionary. Keep the whole Python example below 220 lines so it demonstrates framework flow rather than architecture ceremony.

- [ ] **Step 4: Write lesson READMEs**

Each lesson uses the shared headings and a two-column Spring-to-Python comparison. Cover `@RestController`/`APIRouter`, request validation/Pydantic, Spring DI/explicit construction plus `Depends`, `@ControllerAdvice`/exception handlers, async I/O, JPA/SQLAlchemy unit-of-work semantics, PostgreSQL boundaries, pytest/HTTPX, and Docker runtime packaging. Every comparison includes at least one non-equivalence statement.

- [ ] **Step 5: Run scoped checks and commit**

Run: `uv run pytest modules/02_python_backend/examples -q`

Run: `uv run ruff check modules/02_python_backend`

Run: `uv run mypy modules/02_python_backend/examples`

Commit with message `docs: add production Python backend lessons`.

### Task 2: Pydantic, routing, dependencies, errors, and async exercises

**Files:**
- Create: `modules/02_python_backend/02_pydantic/exercises/transaction_contract/README.md`
- Create: `modules/02_python_backend/02_pydantic/exercises/transaction_contract/starter.py`
- Create: `modules/02_python_backend/02_pydantic/exercises/transaction_contract/test_starter.py`
- Create: `modules/02_python_backend/03_architecture_dependencies/exercises/payment_router/README.md`
- Create: `modules/02_python_backend/03_architecture_dependencies/exercises/payment_router/starter.py`
- Create: `modules/02_python_backend/03_architecture_dependencies/exercises/payment_router/test_starter.py`
- Create: `modules/02_python_backend/04_config_errors_logging/exercises/error_mapping/README.md`
- Create: `modules/02_python_backend/04_config_errors_logging/exercises/error_mapping/starter.py`
- Create: `modules/02_python_backend/04_config_errors_logging/exercises/error_mapping/test_starter.py`
- Create: `modules/02_python_backend/05_async_endpoints/exercises/provider_fanout/README.md`
- Create: `modules/02_python_backend/05_async_endpoints/exercises/provider_fanout/starter.py`
- Create: `modules/02_python_backend/05_async_endpoints/exercises/provider_fanout/test_starter.py`

**Interfaces:**
- Produces `TransactionCreate` with decimal amount, three-letter uppercase currency, merchant, timezone-aware timestamp, and forbidden extra fields.
- Produces `build_payment_router(service: PaymentService) -> APIRouter`, where `POST /payments` returns 201 and `GET /payments/{payment_id}` returns a response or raises `PaymentNotFound`.
- Produces `register_payment_exception_handlers(app: FastAPI) -> None` mapping `PaymentNotFound` to 404 and `PaymentConflict` to 409 with stable `code`, `message`, and `request_id` fields.
- Produces `fetch_provider_quotes(gateways: Sequence[QuoteGateway], request: QuoteRequest) -> list[Quote]`, preserving gateway order while running I/O concurrently.

- [ ] **Step 1: Write Pydantic model tests**

Pin valid serialization, exact Decimal preservation, lowercase currency normalization or rejection according to the README's explicit choice, non-positive amount rejection, unknown currency rejection, naive timestamp rejection, extra-field rejection, and JSON schema examples. Call the student model factory through `exercise_call` when its boundary remains absent.

- [ ] **Step 2: Write router and error-handler tests**

Use `TestClient` with a deterministic fake service. Pin status codes, response model filtering, one service call with the validated model, missing-payment mapping, conflict mapping, request ID propagation, and dependency isolation between two application instances. Configure the starter app so propagated `NotImplementedError` reaches `exercise_call` instead of becoming an unexplained 500 assertion.

- [ ] **Step 3: Write async fan-out tests**

Use `asyncio.Event` gates to prove all gateway calls start before any is released. Assert input-order results, empty input, and cancellation/exception propagation. Do not use elapsed-time thresholds.

- [ ] **Step 4: Add starter modules and concise instructions**

Every module defines the required protocol and domain records locally. The payment router receives its service explicitly; `Depends` appears only in the exercise extension that wires request-scoped composition. Logging instructions require structured fields and forbid payment card/account data.

- [ ] **Step 5: Run exercise and quality gates**

Run: `uv run pytest modules/02_python_backend/02_pydantic/exercises modules/02_python_backend/03_architecture_dependencies/exercises modules/02_python_backend/04_config_errors_logging/exercises modules/02_python_backend/05_async_endpoints/exercises -q -rx`

Run: `uv run ruff check modules/02_python_backend`

Run: `uv run mypy modules/02_python_backend`

Expected: examples pass; starter boundaries are expected-incomplete; unexpected framework errors do not appear.

- [ ] **Step 6: Commit**

Commit with message `feat: add FastAPI service exercises`.

### Task 3: SQLAlchemy and PostgreSQL exercises

**Files:**
- Create: `modules/02_python_backend/06_sqlalchemy/exercises/transaction_repository/README.md`
- Create: `modules/02_python_backend/06_sqlalchemy/exercises/transaction_repository/starter.py`
- Create: `modules/02_python_backend/06_sqlalchemy/exercises/transaction_repository/test_starter.py`
- Create: `modules/02_python_backend/07_postgresql/exercises/postgres_query/README.md`
- Create: `modules/02_python_backend/07_postgresql/exercises/postgres_query/starter.py`
- Create: `modules/02_python_backend/07_postgresql/exercises/postgres_query/test_starter.py`
- Create: `modules/02_python_backend/07_postgresql/exercises/postgres_query/test_postgres.py`
- Create: `modules/02_python_backend/09_docker_delivery/Dockerfile.example`
- Create: `modules/02_python_backend/09_docker_delivery/compose.example.yaml`

**Interfaces:**
- Produces SQLAlchemy 2.x `Base`, `TransactionRecord`, and `SqlAlchemyTransactionRepository.add/get/list_by_user`.
- Produces `daily_currency_totals(session: Session, day: date) -> list[CurrencyTotal]` using a database aggregation rather than loading all rows.

- [ ] **Step 1: Write SQLite repository tests**

Create a temporary SQLite engine per test. Pin insert/get round trip, decimal values, timezone-aware conversion policy, unknown ID, user filtering, deterministic ordering, rollback after an integrity error, and session closure through the provided context-manager fixture.

- [ ] **Step 2: Write database-agnostic query tests**

Seed two days and three currencies, assert only the requested day is aggregated, totals are decimal, and output sorts by currency. Inspect emitted SQL or statement structure to ensure aggregation occurs in SQL.

- [ ] **Step 3: Write opt-in PostgreSQL test**

Mark the test `postgres`. Read only `ROADMAP_POSTGRES_URL`; if absent, skip with `Set ROADMAP_POSTGRES_URL and run: docker compose up -d postgres`. Use a unique table suffix or transaction rollback so the test is isolated. Pin PostgreSQL decimal and timezone behavior without depending on preexisting data.

- [ ] **Step 4: Add starters and deployment examples**

Use `Mapped[...]`, `mapped_column`, `select`, and context-managed sessions. The Dockerfile example uses a supported slim Python image, installs uv, syncs from the lock file without dev dependencies, runs as a non-root user, and documents—but does not hard-code—the application module. The Compose example exposes PostgreSQL only for local learning and uses values mirrored in a later `.env.example`.

- [ ] **Step 5: Run database gates**

Run: `uv run pytest modules/02_python_backend/06_sqlalchemy modules/02_python_backend/07_postgresql -q -rx`

Run: `uv run pytest -m postgres modules/02_python_backend/07_postgresql -q -rs`

Expected without a configured database: starter cases are expected-incomplete and PostgreSQL cases skip with the documented reason.

- [ ] **Step 6: Commit**

Commit with message `feat: add persistence learning exercises`.

### Task 4: Testing lesson exercises and module gate

**Files:**
- Create: `modules/02_python_backend/08_api_integration_testing/exercises/api_test_review/README.md`
- Create: `modules/02_python_backend/08_api_integration_testing/exercises/api_test_review/review_me.py`
- Create: `modules/02_python_backend/08_api_integration_testing/exercises/api_test_review/test_characterization.py`
- Create: `modules/02_python_backend/tests/test_lesson_contracts.py`

**Interfaces:**
- Produces a deliberately coupled API test fixture for student review while preserving its observable behavior.
- Produces module-level documentation and import contract checks.

- [ ] **Step 1: Add a code-review characterization suite**

Create a passing but poorly isolated fixture that shares mutable service state and overrides dependencies without cleanup. Characterization tests pin the API result. The README asks the student to replace it with yield-based fixture cleanup and per-test app creation, then run the same suite repeatedly with `pytest-repeat` omitted; order independence is checked by parametrized invocation order instead.

- [ ] **Step 2: Add lesson contract tests**

Verify all nine README headings, Spring comparison blocks, self-check counts, exercise links, and Docker/PostgreSQL opt-in warnings. Import every starter module to catch framework and typing drift.

- [ ] **Step 3: Run the full module gate**

Run: `uv run pytest modules/02_python_backend -q -rx`

Run: `uv run ruff check modules/02_python_backend`

Run: `uv run ruff format --check modules/02_python_backend`

Run: `uv run mypy modules/02_python_backend --exclude 'review_me.py'`

Expected: no unexpected failures and PostgreSQL remains optional.

- [ ] **Step 4: Commit**

Commit with message `feat: complete Python backend learning module`.
