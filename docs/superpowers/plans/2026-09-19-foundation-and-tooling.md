# Foundation and Learning Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the reproducible Python project, expected-incomplete exercise behavior, curriculum catalog, learning CLI, shared documentation, and future-module placeholders.

**Architecture:** A small installed package under `src/roadmap_tools` owns only cross-cutting catalog and test helpers. Curriculum metadata is declarative TOML, the command wrapper in `scripts/learn.py` delegates to package code, and documentation is plain Markdown. No curriculum algorithm lives in the tooling package.

**Tech Stack:** Python 3.12+, uv, pytest, Ruff, mypy, standard-library `argparse`, `tomllib`, `pathlib`, `difflib`, and `subprocess`

**Spec:** `docs/superpowers/specs/2026-09-19-ai-engineer-roadmap-design.md`

## Global Constraints

- Use the global constraints and Review Focus in `2026-09-19-ai-engineer-roadmap-implementation.md`.
- Keep every public tooling function typed and independently testable.
- The learning CLI may spawn only `sys.executable -m pytest` with catalog-owned paths.
- The environment validator reports corrective commands but does not install software or mutate the environment.

## Review Focus

- `exercise_call` catches only `NotImplementedError`, and all other exceptions propagate.
- Catalog paths are relative, normalized, exist under the repository root, and cannot escape with `..`.
- Duplicate lesson or exercise identifiers fail catalog loading with both conflicting entries named.
- CLI subprocess exit codes are returned unchanged to the caller.
- Windows paths containing spaces are passed as argument-list elements, never shell-concatenated.

---

### Task 1: Reproducible project and exercise test helper

**Files:**
- Create: `.python-version`
- Create: `.gitattributes`
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `src/roadmap_tools/__init__.py`
- Create: `src/roadmap_tools/exercise.py`
- Create: `tests/tooling/test_exercise.py`

**Interfaces:**
- Produces: `roadmap_tools.exercise.exercise_call(operation: Callable[..., T], /, *args: object, **kwargs: object) -> T`
- Produces: the `student_exercise` pytest marker and root pytest configuration.

- [ ] **Step 1: Write tests for the three exercise states**

Create `tests/tooling/test_exercise.py` with a completed operation assertion, an expected-incomplete test that calls an operation raising `NotImplementedError`, and a propagation test for `ValueError`:

```python
from collections.abc import Callable

import pytest

from roadmap_tools.exercise import exercise_call


def test_exercise_call_returns_completed_value() -> None:
    assert exercise_call(lambda value: value * 2, 21) == 42


@pytest.mark.student_exercise
def test_unimplemented_operation_is_expected_incomplete() -> None:
    def unfinished() -> None:
        raise NotImplementedError("student boundary")

    exercise_call(unfinished)


def test_exercise_call_does_not_hide_other_errors() -> None:
    operation: Callable[[], None] = lambda: (_ for _ in ()).throw(ValueError("bad input"))
    with pytest.raises(ValueError, match="bad input"):
        exercise_call(operation)
```

- [ ] **Step 2: Run the focused tests and confirm the missing-package failure**

Run: `python -m pytest tests/tooling/test_exercise.py -q`

Expected: collection fails because `roadmap_tools` does not exist.

- [ ] **Step 3: Add project metadata and dependencies**

Create a PEP 621 `pyproject.toml` named `ai-engineer-roadmap`, requiring Python `>=3.12`, using the `uv_build` backend, and declaring runtime dependencies for FastAPI, Pydantic, Pydantic Settings, SQLAlchemy, psycopg binary, HTTPX, NumPy, and Pandas. Add a `dev` dependency group containing pytest, pytest-asyncio, Ruff, mypy, JupyterLab, ipykernel, nbformat, and pandas typing stubs when available for the resolved interpreter.

Configure pytest with `testpaths = ["tests", "modules", "projects"]`, `xfail_strict = true`, and the `student_exercise` and `postgres` markers. Configure Ruff for Python 3.12 with an 100-character line length and enable `E`, `F`, `I`, `B`, `UP`, `SIM`, `RUF`, and `PT`. Configure mypy with Python 3.12, strict checks, and explicit exclusions for notebook JSON and intentionally broken review fixtures.

Set `.python-version` to exactly `3.12`. Set `.gitattributes` to normalize text to LF while preserving CRLF for `.ps1` and binary treatment for images and notebooks. Ignore `.venv`, PyCharm metadata, Python caches, pytest/mypy/Ruff caches, coverage output, `.env`, local database files, notebook checkpoints, generated reports, and derived datasets.

- [ ] **Step 4: Implement the narrow expected-incomplete adapter**

Create `src/roadmap_tools/exercise.py`:

```python
from collections.abc import Callable
from typing import TypeVar

import pytest

T = TypeVar("T")


def exercise_call(
    operation: Callable[..., T], /, *args: object, **kwargs: object
) -> T:
    try:
        return operation(*args, **kwargs)
    except NotImplementedError as exc:
        pytest.xfail(f"Exercise not implemented yet: {exc}")
```

Export `exercise_call` from `roadmap_tools.__init__` and add a concise module docstring explaining that this helper belongs only in tests.

- [ ] **Step 5: Create the environment and run the focused tests**

Run: `uv sync --all-groups`

Run: `uv run pytest tests/tooling/test_exercise.py -q -rx`

Expected: two passed and one expected-incomplete test, exit code 0.

- [ ] **Step 6: Run static checks and commit**

Run: `uv run ruff check pyproject.toml src tests/tooling`

Run: `uv run ruff format --check src tests/tooling`

Run: `uv run mypy src tests/tooling`

Commit files from this task with message `build: establish Python learning environment`.

### Task 2: Validated curriculum catalog

**Files:**
- Create: `curriculum.toml`
- Create: `src/roadmap_tools/catalog.py`
- Create: `tests/tooling/test_catalog.py`

**Interfaces:**
- Consumes: repository root as a resolved `Path`.
- Produces: `CatalogItem(identifier: str, title: str, kind: Literal["lesson", "exercise", "project"], readme: Path, tests: tuple[Path, ...])`.
- Produces: `Catalog.load(repository_root: Path, catalog_path: Path | None = None) -> Catalog`.
- Produces: `Catalog.get(identifier: str) -> CatalogItem` and `Catalog.suggest(identifier: str) -> tuple[str, ...]`.

- [ ] **Step 1: Write catalog validation tests**

Use `tmp_path` to create a minimal valid TOML catalog and existing README/test files. Pin successful loading, duplicate identifier rejection, missing paths, `../outside` traversal rejection, and close-match suggestions for `python-collectons` returning `python-collections`.

The valid test record is:

```toml
[[items]]
id = "python-collections"
title = "Collections"
kind = "lesson"
readme = "modules/01_python_core/02_collections/README.md"
tests = ["modules/01_python_core/02_collections"]
```

- [ ] **Step 2: Run catalog tests and confirm the import failure**

Run: `uv run pytest tests/tooling/test_catalog.py -q`

Expected: failure because `roadmap_tools.catalog` does not exist.

- [ ] **Step 3: Implement immutable catalog models and path validation**

Use frozen dataclasses and `tomllib`. Resolve every catalog-owned path relative to the supplied repository root and reject a path unless `resolved_path.is_relative_to(repository_root)` is true. Raise `CatalogError` with the identifier and offending field for malformed records, unknown kinds, duplicate IDs, missing files, empty test target lists, or escaping paths. Use `difflib.get_close_matches` with at most three results.

Populate `curriculum.toml` with the module and project identifiers defined in all subplans. Paths may point to files created by later waves; catalog validation tests use temporary fixtures until integration.

- [ ] **Step 4: Run catalog tests and type checks**

Run: `uv run pytest tests/tooling/test_catalog.py -q`

Run: `uv run mypy src/roadmap_tools/catalog.py tests/tooling/test_catalog.py`

Expected: all catalog tests pass.

- [ ] **Step 5: Commit**

Commit `curriculum.toml`, catalog code, and tests with message `feat: add validated curriculum catalog`.

### Task 3: Learning command-line interface

**Files:**
- Create: `src/roadmap_tools/cli.py`
- Create: `scripts/learn.py`
- Create: `tests/tooling/test_cli.py`

**Interfaces:**
- Consumes: `Catalog.load`, `Catalog.get`, and `Catalog.suggest`.
- Produces: `main(argv: Sequence[str] | None = None, repository_root: Path | None = None) -> int`.
- Produces commands: `validate-env`, `list`, `status`, and `test IDENTIFIER`.

- [ ] **Step 1: Write CLI tests with injected subprocess runner**

Test that `list` orders items by catalog order; `status` reports `[ ]`, `[~]`, and `[x]` parsed from a temporary `progress.md`; an unknown ID exits 2 and prints a suggestion; `test` invokes exactly `[sys.executable, "-m", "pytest", *item.tests]`; and subprocess exit code 5 is returned as 5. Include a repository path containing a space.

- [ ] **Step 2: Run tests and confirm they fail on the absent CLI**

Run: `uv run pytest tests/tooling/test_cli.py -q`

Expected: import failure for `roadmap_tools.cli`.

- [ ] **Step 3: Implement commands without shell evaluation**

Build the parser with `argparse`. Accept an injectable `run_process: Callable[[Sequence[str]], int]` internally so tests do not launch pytest. `validate-env` checks `sys.version_info >= (3, 12)`, locates `uv` with `shutil.which`, reports `sys.executable`, and returns 1 with the exact corrective command `uv sync --all-groups` when a prerequisite is missing. `status` parses only checklist entries matching `- [ ]`, `- [~]`, or `- [x]` and never writes the file.

Make `scripts/learn.py` a thin executable wrapper that resolves the repository root from its own location and exits with `main(repository_root=root)`.

- [ ] **Step 4: Run CLI tests and manual commands**

Run: `uv run pytest tests/tooling/test_cli.py -q`

Run: `uv run python scripts/learn.py validate-env`

Run: `uv run python scripts/learn.py list`

Expected: tests pass; environment validation exits zero; list prints known entries without a traceback.

- [ ] **Step 5: Run quality checks and commit**

Run: `uv run ruff check src scripts tests/tooling`

Run: `uv run ruff format --check src scripts tests/tooling`

Run: `uv run mypy src scripts tests/tooling`

Commit with message `feat: add learning workflow CLI`.

### Task 4: Shared documentation and future roadmap

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Create: `progress.md`
- Create: `docs/roadmap.md`
- Create: `docs/setup.md`
- Create: `docs/learning-rules.md`
- Create: `docs/testing-exercises.md`
- Create: `docs/java-to-python-cheatsheet.md`
- Create: `modules/04_machine_learning/README.md`
- Create: `modules/05_llm_engineering/README.md`
- Create: `modules/06_rag/README.md`
- Create: `modules/07_agents/README.md`
- Create: `modules/08_production_ai/README.md`
- Create: `tests/tooling/test_documentation.py`

**Interfaces:**
- Consumes: the exact commands and paths produced by Tasks 1–3.
- Produces: human-facing entry points and manually editable progress checkboxes.

- [ ] **Step 1: Write documentation contract tests**

Test that every root README command from the final interface contract appears verbatim; all relative Markdown links in root/shared docs resolve; progress contains an entry for every catalog lesson; and each future module README includes scope, prerequisites, planned outcomes, and the sentence `Exercises are intentionally deferred.`

- [ ] **Step 2: Run contract tests and observe missing-document failures**

Run: `uv run pytest tests/tooling/test_documentation.py -q`

Expected: failures list the absent documentation files.

- [ ] **Step 3: Write Windows-first setup and learning guidance**

Document `uv sync --all-groups`, `.venv\Scripts\python.exe` selection in PyCharm, repository-root working directories, the expected-incomplete test state, scoped tests, Ruff, mypy, manual progress editing, and the first lesson path. The cheat sheet must cover Java record, interface, Stream API, `Optional<T>`, JUnit, Maven/Gradle, Bean Validation, try-with-resources, and `Executor`/`CompletableFuture`, with a semantic-difference column for every row.

Use the MIT license. Do not claim Modules 04–08 are implemented.

- [ ] **Step 4: Run documentation and tooling suites**

Run: `uv run pytest tests/tooling -q -rx`

Run: `uv run ruff check .`

Run: `uv run ruff format --check .`

Expected: documentation contract tests pass and the sole expected-incomplete result remains the helper's intentional test.

- [ ] **Step 5: Commit**

Commit shared documentation and future module files with message `docs: add roadmap and learning workflow`.
