# Module 01 Python Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the complete Python-for-Java-developers curriculum and a fully runnable first sprint with ten coding exercises, two debugging tasks, two code reviews, and one mini-feature.

**Architecture:** Eleven numbered lesson folders form the reading sequence. Exercises are colocated with the concept that owns them, import only their own starter modules plus `roadmap_tools.exercise`, and use business-domain inputs. Later lessons remain concise but runnable so the module is complete without overwhelming the first sprint.

**Tech Stack:** Python 3.12+, pytest, pytest-asyncio, standard-library typing, dataclasses, pathlib, csv, json, asyncio, and unittest.mock

**Spec:** `docs/superpowers/specs/2026-09-19-ai-engineer-roadmap-design.md`

## Global Constraints

- Use the global constraints and Review Focus in `2026-09-19-ai-engineer-roadmap-implementation.md`.
- Do not explain variables, loops, HTTP, databases, or OOP from first principles.
- Every lesson README uses the exact shared lesson headings and contains 5–10 self-check questions.
- Every exercise README names the editable starter file, difficulty, 10–90 minute estimate, acceptance criteria, command, and optional hints.
- Starter functions contain signatures, docstrings, input validation requirements, and `raise NotImplementedError("Implement …")`; they contain no target algorithm.

## Review Focus

- Empty iterables return neutral results rather than raising unless the README defines an invalid input.
- Repeated iterables may be one-shot generators; an exercise must not silently consume them twice.
- Decimal values are never converted through binary floating point in payment-domain tasks.
- Sorting is deterministic when primary keys tie.
- Async examples prove concurrency with controlled events or mocked waits, never wall-clock thresholds alone.

---

### Task 1: Lesson sequence and runnable examples

**Files:**
- Create: `modules/01_python_core/README.md`
- Create: `modules/01_python_core/00_environment/README.md`
- Create: `modules/01_python_core/00_environment/example.py`
- Create: `modules/01_python_core/01_object_model/README.md`
- Create: `modules/01_python_core/01_object_model/example.py`
- Create: `modules/01_python_core/02_collections/README.md`
- Create: `modules/01_python_core/02_collections/example.py`
- Create: `modules/01_python_core/03_functions/README.md`
- Create: `modules/01_python_core/03_functions/example.py`
- Create: `modules/01_python_core/04_typing/README.md`
- Create: `modules/01_python_core/04_typing/example.py`
- Create: `modules/01_python_core/05_data_modeling/README.md`
- Create: `modules/01_python_core/05_data_modeling/example.py`
- Create: `modules/01_python_core/06_exceptions_io/README.md`
- Create: `modules/01_python_core/06_exceptions_io/example.py`
- Create: `modules/01_python_core/07_iterators_generators/README.md`
- Create: `modules/01_python_core/07_iterators_generators/example.py`
- Create: `modules/01_python_core/08_decorators/README.md`
- Create: `modules/01_python_core/08_decorators/example.py`
- Create: `modules/01_python_core/09_testing/README.md`
- Create: `modules/01_python_core/09_testing/example.py`
- Create: `modules/01_python_core/10_asyncio/README.md`
- Create: `modules/01_python_core/10_asyncio/example.py`
- Create: `modules/01_python_core/tests/test_examples.py`

**Interfaces:**
- Produces: one `main() -> None` per example with no network, database, or filesystem side effects outside a pytest temporary directory.
- Produces catalog lesson IDs `python-environment`, `python-object-model`, `python-collections`, `python-functions`, `python-typing`, `python-data-modeling`, `python-io`, `python-generators`, `python-decorators`, `python-testing`, and `python-asyncio`.

- [ ] **Step 1: Write example smoke tests**

Parametrize all eleven `example.py` paths. Load each with `runpy.run_path`, assert it defines callable `main`, call it, and assert captured stderr is empty. Add focused assertions for object identity versus equality, a lazy generator returning an iterator, a decorator preserving `__name__`, and `asyncio.gather` preserving input order.

- [ ] **Step 2: Run the smoke tests and confirm missing-file failures**

Run: `uv run pytest modules/01_python_core/tests/test_examples.py -q`

Expected: parametrized failures naming the absent lesson examples.

- [ ] **Step 3: Write concise lesson READMEs**

Use the shared headings. The Java mental models are respectively: toolchain/Maven, references and `==`, collections/Stream API, functional interfaces, generics/interfaces, records/POJOs, exceptions/try-with-resources, `Iterable`/streams, annotations/interceptors, JUnit, and `CompletableFuture`. Each Python model section states where the analogy ends. Keep each README under 220 lines and each key-concept paragraph under 120 words.

- [ ] **Step 4: Write examples that do not reveal exercise algorithms**

Use these example scenarios in order: environment facts; mutable support-ticket tags; document-language collection idioms; notification callbacks; an `ExchangeRateProvider` protocol; a frozen `LedgerEntry` dataclass; atomic JSON export with a context manager; streaming log lines; timing a document parser; parametrizing currency validation; and concurrent mocked LLM metadata calls. None may implement transaction duplicate detection, grouping, report generation, or the other sprint targets.

- [ ] **Step 5: Run lesson checks**

Run: `uv run pytest modules/01_python_core/tests/test_examples.py -q`

Run: `uv run ruff check modules/01_python_core`

Run: `uv run mypy modules/01_python_core --exclude 'exercises/.*/broken.py'`

Expected: all example checks pass.

- [ ] **Step 6: Commit**

Commit the lesson sequence with message `docs: add Python core lesson sequence`.

### Task 2: Collections, comprehensions, slicing, and unpacking exercises

**Files:**
- Create: `modules/01_python_core/02_collections/exercises/detect_duplicates/README.md`
- Create: `modules/01_python_core/02_collections/exercises/detect_duplicates/starter.py`
- Create: `modules/01_python_core/02_collections/exercises/detect_duplicates/test_starter.py`
- Create: `modules/01_python_core/02_collections/exercises/group_by_user/README.md`
- Create: `modules/01_python_core/02_collections/exercises/group_by_user/starter.py`
- Create: `modules/01_python_core/02_collections/exercises/group_by_user/test_starter.py`
- Create: `modules/01_python_core/02_collections/exercises/provider_frequency/README.md`
- Create: `modules/01_python_core/02_collections/exercises/provider_frequency/starter.py`
- Create: `modules/01_python_core/02_collections/exercises/provider_frequency/test_starter.py`
- Create: `modules/01_python_core/02_collections/exercises/sort_payments/README.md`
- Create: `modules/01_python_core/02_collections/exercises/sort_payments/starter.py`
- Create: `modules/01_python_core/02_collections/exercises/sort_payments/test_starter.py`
- Create: `modules/01_python_core/02_collections/exercises/filter_project_events/README.md`
- Create: `modules/01_python_core/02_collections/exercises/filter_project_events/starter.py`
- Create: `modules/01_python_core/02_collections/exercises/filter_project_events/test_starter.py`
- Create: `modules/01_python_core/02_collections/exercises/slice_windows/README.md`
- Create: `modules/01_python_core/02_collections/exercises/slice_windows/starter.py`
- Create: `modules/01_python_core/02_collections/exercises/slice_windows/test_starter.py`
- Create: `modules/01_python_core/02_collections/exercises/unpack_settlements/README.md`
- Create: `modules/01_python_core/02_collections/exercises/unpack_settlements/starter.py`
- Create: `modules/01_python_core/02_collections/exercises/unpack_settlements/test_starter.py`

**Interfaces:**
- Consumes: `roadmap_tools.exercise.exercise_call` in tests.
- Produces the following typed student boundaries:

```python
def find_duplicate_ids(transactions: Iterable[Mapping[str, object]]) -> set[str]: ...
def group_amounts_by_user(transactions: Iterable[tuple[str, Decimal]]) -> dict[str, list[Decimal]]: ...
def provider_frequencies(providers: Iterable[str]) -> dict[str, int]: ...
def sort_payments(payments: Iterable[PaymentRow]) -> list[PaymentRow]: ...
def active_event_ids(events: Iterable[EventRow], allowed_types: set[str]) -> list[str]: ...
def transaction_windows(transaction_ids: Sequence[str], size: int) -> list[tuple[str, ...]]: ...
def parse_settlement(row: Sequence[str]) -> tuple[str, Decimal, str]: ...
```

`PaymentRow` and `EventRow` are `TypedDict` definitions colocated in their starter modules. Payments sort by descending `amount`, then ascending `timestamp`, then ascending `id`. Settlement rows contain exactly transaction ID, decimal amount text, and currency.

- [ ] **Step 1: Write seven failing student test suites**

Every behavioral assertion calls the boundary through `exercise_call`. Pin these cases:

| Exercise | Required assertions |
|---|---|
| `detect_duplicates` | repeated IDs, unique IDs, empty generator, missing/string-invalid ID |
| `group_by_user` | input order preserved within user, decimals retained, generator input, empty input |
| `provider_frequency` | counts and insertion order, empty input, mixed case remains distinct |
| `sort_payments` | three-key order, original list unchanged, generator input, empty input |
| `filter_project_events` | allowed active events only, output IDs only, absent type, empty allowed set |
| `slice_windows` | full and final partial windows, size larger than input, size 1, non-positive size error |
| `unpack_settlements` | valid decimal, wrong field count, invalid decimal, blank currency |

- [ ] **Step 2: Run the suites and verify expected-incomplete status**

Run: `uv run pytest modules/01_python_core/02_collections/exercises -q -rx`

Expected: student tests report expected-incomplete and exit zero; test collection has no import errors.

- [ ] **Step 3: Write starter modules and exercise instructions**

Define all data shapes locally so a student can open one exercise without searching the repository. Validate only contract-level invalid inputs before the `NotImplementedError` boundary when validation itself is not the lesson target. Hints may name relevant Python constructs—set membership, `dict.setdefault`, `Counter`, `sorted(key=...)`, comprehensions, slicing, and unpacking—but may not contain pseudocode for the whole algorithm.

- [ ] **Step 4: Prove the failure model detects an incorrect attempt**

Temporarily replace `provider_frequencies` with `return {}` using an apply/revert patch, run its tests, and observe assertion failures. Restore `raise NotImplementedError`, rerun, and observe expected-incomplete results with exit zero.

- [ ] **Step 5: Run quality checks and commit**

Run: `uv run pytest modules/01_python_core/02_collections/exercises -q -rx`

Run: `uv run ruff check modules/01_python_core/02_collections`

Run: `uv run mypy modules/01_python_core/02_collections`

Commit with message `feat: add first-sprint collection exercises`.

### Task 3: Functions and typing exercises

**Files:**
- Create: `modules/01_python_core/03_functions/exercises/configurable_filter/README.md`
- Create: `modules/01_python_core/03_functions/exercises/configurable_filter/starter.py`
- Create: `modules/01_python_core/03_functions/exercises/configurable_filter/test_starter.py`
- Create: `modules/01_python_core/03_functions/exercises/combine_responses/README.md`
- Create: `modules/01_python_core/03_functions/exercises/combine_responses/starter.py`
- Create: `modules/01_python_core/03_functions/exercises/combine_responses/test_starter.py`
- Create: `modules/01_python_core/04_typing/exercises/payment_processor_protocol/README.md`
- Create: `modules/01_python_core/04_typing/exercises/payment_processor_protocol/starter.py`
- Create: `modules/01_python_core/04_typing/exercises/payment_processor_protocol/test_starter.py`

**Interfaces:**
- Produces:

```python
TransactionPredicate: TypeAlias = Callable[[TransactionRow], bool]
def make_transaction_filter(*, minimum: Decimal = Decimal("0"), currencies: frozenset[str] | None = None, predicate: TransactionPredicate | None = None) -> TransactionPredicate: ...
def combine_provider_responses(provider_names: Sequence[str], responses: Iterable[ProviderResponse]) -> list[IndexedProviderResponse]: ...
class PaymentProcessor(Protocol):
    def authorize(self, payment: Payment) -> Authorization: ...
def authorize_payment(processor: PaymentProcessor, payment: Payment) -> Authorization: ...
```

The combined response records include a one-based index, provider name, and response. Length mismatches raise `ValueError`. `Payment`, `Authorization`, and response rows are frozen dataclasses or `TypedDict` values defined in the starter file.

- [ ] **Step 1: Write function and protocol tests**

Pin keyword-only construction, `None` currency meaning no restriction, predicate composition, captured immutable configuration, one-shot response generators, mismatch errors, structural protocol compatibility, and propagation of a processor's domain exception. Run every student boundary through `exercise_call`.

- [ ] **Step 2: Run tests and confirm only expected-incomplete outcomes**

Run: `uv run pytest modules/01_python_core/03_functions/exercises modules/01_python_core/04_typing/exercises -q -rx`

- [ ] **Step 3: Add starter code and instructions**

Use Python 3.12 built-in generics and `type` aliases only where supported by mypy in the resolved environment. Explain why `Protocol` expresses structural compatibility rather than Java-style nominal implementation. Keep lambda usage limited to examples and avoid requiring it when a named predicate communicates intent better.

- [ ] **Step 4: Run static and behavioral checks**

Run: `uv run pytest modules/01_python_core/03_functions/exercises modules/01_python_core/04_typing/exercises -q -rx`

Run: `uv run ruff check modules/01_python_core/03_functions modules/01_python_core/04_typing`

Run: `uv run mypy modules/01_python_core/03_functions modules/01_python_core/04_typing`

- [ ] **Step 5: Commit**

Commit with message `feat: add first-sprint function and typing exercises`.

### Task 4: Debugging and code-review tasks

**Files:**
- Create: `modules/01_python_core/03_functions/debugging/mutable_defaults/README.md`
- Create: `modules/01_python_core/03_functions/debugging/mutable_defaults/broken.py`
- Create: `modules/01_python_core/03_functions/debugging/mutable_defaults/test_behavior.py`
- Create: `modules/01_python_core/07_iterators_generators/debugging/iterator_exhaustion/README.md`
- Create: `modules/01_python_core/07_iterators_generators/debugging/iterator_exhaustion/broken.py`
- Create: `modules/01_python_core/07_iterators_generators/debugging/iterator_exhaustion/test_behavior.py`
- Create: `modules/01_python_core/02_collections/code_review/java_shaped_grouping/README.md`
- Create: `modules/01_python_core/02_collections/code_review/java_shaped_grouping/review_me.py`
- Create: `modules/01_python_core/02_collections/code_review/java_shaped_grouping/test_characterization.py`
- Create: `modules/01_python_core/03_functions/code_review/stateful_report/README.md`
- Create: `modules/01_python_core/03_functions/code_review/stateful_report/review_me.py`
- Create: `modules/01_python_core/03_functions/code_review/stateful_report/test_characterization.py`

**Interfaces:**
- Produces: intentionally incorrect `append_audit_tag(tag: str, tags: list[str] = []) -> list[str]` and `summarize_amounts(amounts: Iterable[Decimal]) -> tuple[int, Decimal]`.
- Produces: behavior-preserving review targets `group_transactions(rows)` and `ReportBuilder.build(rows)`.

- [ ] **Step 1: Write debugging tests as non-strict expected failures**

Mark only debugging behavior tests with `@pytest.mark.xfail(reason="intentional broken starter", strict=False)`. For mutable defaults, call twice and assert isolated results. For iterator exhaustion, pass a generator and assert both the correct count and sum. Exercise READMEs require the command with `--runxfail`, so the broken version fails and a corrected version passes.

- [ ] **Step 2: Write characterization tests for review tasks**

Pin ordering, decimals, empty input, and non-mutation. These tests pass before refactoring. The READMEs ask the student to remove index-based loops, redundant temporary collections, boolean flags, and cross-call object state while keeping the tests green.

- [ ] **Step 3: Create the intentional inputs and instructions**

Keep each `broken.py` and `review_me.py` syntactically valid and importable. State the observed symptom, reproduction command, allowed edit file, behavior that must remain, and a self-review checklist. Do not state the corrected implementation.

- [ ] **Step 4: Verify both execution modes**

Run: `uv run pytest modules/01_python_core/03_functions/debugging modules/01_python_core/07_iterators_generators/debugging -q -rx`

Expected: two xfails, exit zero.

Run each debugging suite with `--runxfail`.

Expected: failures demonstrating the two defects.

Run: `uv run pytest modules/01_python_core/02_collections/code_review modules/01_python_core/03_functions/code_review -q`

Expected: characterization tests pass.

- [ ] **Step 5: Commit**

Commit with message `feat: add Python debugging and review tasks`.

### Task 5: Transaction analytics mini-feature and later-lesson practice

**Files:**
- Create: `modules/01_python_core/mini_features/transaction_report/README.md`
- Create: `modules/01_python_core/mini_features/transaction_report/report.py`
- Create: `modules/01_python_core/mini_features/transaction_report/test_report.py`
- Create: `modules/01_python_core/05_data_modeling/exercises/payment_model/README.md`
- Create: `modules/01_python_core/05_data_modeling/exercises/payment_model/starter.py`
- Create: `modules/01_python_core/05_data_modeling/exercises/payment_model/test_starter.py`
- Create: `modules/01_python_core/06_exceptions_io/exercises/json_export/README.md`
- Create: `modules/01_python_core/06_exceptions_io/exercises/json_export/starter.py`
- Create: `modules/01_python_core/06_exceptions_io/exercises/json_export/test_starter.py`
- Create: `modules/01_python_core/07_iterators_generators/exercises/stream_transactions/README.md`
- Create: `modules/01_python_core/07_iterators_generators/exercises/stream_transactions/starter.py`
- Create: `modules/01_python_core/07_iterators_generators/exercises/stream_transactions/test_starter.py`
- Create: `modules/01_python_core/08_decorators/exercises/retry_gateway/README.md`
- Create: `modules/01_python_core/08_decorators/exercises/retry_gateway/starter.py`
- Create: `modules/01_python_core/08_decorators/exercises/retry_gateway/test_starter.py`
- Create: `modules/01_python_core/09_testing/exercises/mock_provider/README.md`
- Create: `modules/01_python_core/09_testing/exercises/mock_provider/starter.py`
- Create: `modules/01_python_core/09_testing/exercises/mock_provider/test_starter.py`
- Create: `modules/01_python_core/10_asyncio/exercises/fetch_quotes/README.md`
- Create: `modules/01_python_core/10_asyncio/exercises/fetch_quotes/starter.py`
- Create: `modules/01_python_core/10_asyncio/exercises/fetch_quotes/test_starter.py`

**Interfaces:**
- Produces: `build_transaction_report(rows: Iterable[TransactionRow]) -> TransactionReport`, where the frozen report contains transaction count, total `Decimal`, totals by currency, counts by status, and the top three merchants by total amount with alphabetical tie-breaking.
- Produces one focused starter boundary per later lesson using the concept named by its folder.

- [ ] **Step 1: Write the mini-feature acceptance tests**

Pin a generator input, mixed currencies, repeated merchants, deterministic tie-breaking, empty input, preservation of decimals, and non-mutation. Route the report call through `exercise_call`.

- [ ] **Step 2: Write later-lesson practice tests**

Pin frozen dataclass invariants and positive amounts; atomic JSON export and path cleanup on serialization failure; lazy reading from an iterator; retry count and preserved decorator metadata; one provider call asserted with a mock; and async result ordering plus exception propagation using controlled coroutine events.

- [ ] **Step 3: Run tests and verify the untouched state**

Run: `uv run pytest modules/01_python_core/mini_features modules/01_python_core/05_data_modeling modules/01_python_core/06_exceptions_io modules/01_python_core/07_iterators_generators modules/01_python_core/08_decorators modules/01_python_core/09_testing modules/01_python_core/10_asyncio -q -rx`

Expected: starter behavior is expected-incomplete; no collection or fixture errors occur.

- [ ] **Step 4: Write instructions and starter interfaces**

The mini-feature README gives a 60–90 minute estimate, explicit report schema, deterministic ordering rules, invalid-row policy, command, hints, and ten review questions. Later practice tasks remain 20–45 minutes and do not duplicate the mini-feature.

- [ ] **Step 5: Run the complete Module 01 gate**

Run: `uv run pytest modules/01_python_core -q -rx`

Run: `uv run ruff check modules/01_python_core`

Run: `uv run ruff format --check modules/01_python_core`

Run: `uv run mypy modules/01_python_core --exclude 'debugging/.*/broken.py' --exclude 'code_review/.*/review_me.py'`

Expected: passing examples and characterization tests, visible expected-incomplete student tests, and no unexpected failure.

- [ ] **Step 6: Commit**

Commit with message `feat: complete Python core learning module`.
