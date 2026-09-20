# AI Engineer Roadmap Repository Design

**Date:** 2026-09-19

**Status:** Proposed for implementation

**Repository root:** `C:\ProjectsDirectory\AIML\_road`

**Published repository name:** `ai-engineer-roadmap`

## 1. Purpose and audience

This repository is an active-learning curriculum for an experienced Java and Spring backend engineer moving into Applied AI and AI Engineering. It is simultaneously:

1. a concise curriculum;
2. a set of exercises with automated feedback;
3. a sequence of realistic mini-features;
4. a progressively built banking AI project;
5. a GitHub-ready portfolio artifact.

The material assumes fluency in programming, backend architecture, REST, SQL, testing, dependency injection, OOP, Git, and Docker fundamentals. It does not reteach elementary programming constructs. Java comparisons exist only where they shorten the path to an accurate Python mental model.

The implemented learning scope is Modules 01–03. Modules 04–08 preserve the future roadmap without exercises or implementation content.

## 2. Selected architecture

The repository uses one Python project and one `uv`-managed environment. Lessons remain independent through folders and scoped test commands, while a single toolchain keeps Windows and PyCharm setup simple.

Rejected alternatives:

- Separate Python projects per module create unnecessary environment and configuration duplication.
- A custom lesson engine or web interface adds infrastructure unrelated to learning Python and AI engineering.
- A notebook-only curriculum does not provide the refactoring, testing, packaging, and backend experience required for production AI work.

## 3. Repository layout

```text
ai-engineer-roadmap/
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── progress.md
├── curriculum.toml
├── docs/
│   ├── roadmap.md
│   ├── setup.md
│   ├── learning-rules.md
│   ├── testing-exercises.md
│   ├── java-to-python-cheatsheet.md
│   └── superpowers/
│       ├── specs/
│       └── plans/
├── modules/
│   ├── 01_python_core/
│   ├── 02_python_backend/
│   ├── 03_data_foundations/
│   ├── 04_machine_learning/
│   ├── 05_llm_engineering/
│   ├── 06_rag/
│   ├── 07_agents/
│   └── 08_production_ai/
├── projects/
│   └── banking_ai_lab/
├── datasets/
├── scripts/
├── src/
│   └── roadmap_tools/
└── tests/
```

Each detailed lesson contains a concise `README.md`, runnable examples, starter exercises, and colocated tests where applicable. Reusable repository tooling lives in `src/roadmap_tools`; lesson business logic does not depend on a framework invented for the curriculum.

## 4. Learning-unit contract

Every implemented lesson README contains these sections:

- Goal
- Java mental model
- Python model
- Key concepts
- Example
- Exercises
- Self-check
- Done when

Theory remains concise and operational. Examples use payments, transactions, banking events, APIs, documents, support tickets, or LLM-style I/O. Examples demonstrate the concept without reproducing the exercise algorithm.

Each exercise folder contains:

- `README.md` with goal, difficulty, estimated time, requirements, acceptance criteria, commands, and optional hints;
- starter Python code with types and explicit `NotImplementedError` boundaries;
- pytest tests covering normal behavior, edge cases, and error behavior;
- no solution file, answer branch, or completed implementation in the working tree.

Exercise types are small coding tasks, debugging tasks, code-review tasks, reasoning prompts, and mini-features. The student changes starter code rather than test expectations.

## 5. Module 01: Python for Java developers

Module 01 contains the following lessons:

1. environment and workflow;
2. syntax, references, mutability, identity, equality, truthiness, `None`, and conventions;
3. lists, tuples, sets, dictionaries, slicing, unpacking, comprehensions, membership, sorting, and aggregation idioms;
4. functions as values, argument forms, lambdas, closures, `enumerate`, and `zip`;
5. built-in generic types, unions, optional values, `Callable`, `Literal`, aliases, and `Protocol`;
6. classes, dataclasses, composition, inheritance, ABCs, protocols, and properties;
7. exceptions, context managers, `pathlib`, files, JSON, and CSV;
8. iterables, iterators, generators, generator expressions, and memory behavior;
9. decorators for logging, retry, and timing;
10. pytest fixtures, parametrization, mocks, and exception testing;
11. coroutines, `async`, `await`, the event loop, `asyncio.gather`, and I/O concurrency.

The async lesson explicitly distinguishes cooperative I/O concurrency from threads and CPU parallelism.

### First sprint inventory

The first sprint is immediately usable and contains exactly:

- 10 small coding exercises:
  - detect duplicate transactions;
  - group transactions by user;
  - count payment providers;
  - sort payments using multiple keys;
  - filter and project event records with a comprehension;
  - calculate sliding transaction windows with slicing;
  - unpack settlement records safely;
  - build a configurable transaction filter function;
  - combine provider responses using `zip` and `enumerate`;
  - implement a typed payment-processor protocol boundary;
- 2 debugging tasks:
  - shared mutable default arguments;
  - iterator exhaustion during a two-pass aggregation;
- 2 code-review tasks:
  - Java-shaped transaction grouping;
  - overly stateful report construction;
- 1 mini-feature:
  - transaction analytics report generation from in-memory records.

The sprint covers environment validation, collections, comprehensions, slicing and unpacking, functions, and typing fundamentals. Later Module 01 lessons include smaller practice tasks and examples without duplicating the sprint inventory.

## 6. Module 02: Production Python and FastAPI

Module 02 uses Spring knowledge as a bridge while teaching native FastAPI and Python composition. Its lessons cover:

1. FastAPI application and router fundamentals;
2. Pydantic request, response, and validation models;
3. dependency composition, service boundaries, and repository protocols;
4. settings, structured logging, and exception handlers;
5. async endpoints and I/O boundaries;
6. SQLAlchemy 2.x models, sessions, queries, and migrations concepts;
7. PostgreSQL configuration and persistence;
8. API, service, repository, and integration tests;
9. containerizing the completed service.

The examples map familiar Spring concepts to FastAPI, then state the semantic difference. `Depends` is not presented as a Spring container, modules are not wrapped in classes without a reason, and repository abstractions exist only at external boundaries.

Fast unit and API tests use an in-memory or temporary SQLite database when SQL dialect behavior is irrelevant. PostgreSQL-specific integration tests are explicitly marked and run only when the documented database URL is available. Docker Compose appears only in the backend project stage and is not required for Module 01.

## 7. Module 03: Data foundations

Module 03 combines concise Markdown lessons, Python exercises, and Jupyter notebooks. It covers:

- NumPy arrays, shape, dtype, indexing, masks, reshape, axes, vectorization, broadcasting, aggregation, dot products, and linear-algebra intuition;
- Pandas CSV ingestion, inspection, filtering, `loc`, `iloc`, missing values, duplicates, grouping, aggregation, joins, sorting, datetimes, transformations, categoricals, and data-quality checks;
- mean, median, variance, standard deviation, percentiles, distributions, correlation, conditional probability, and Bayesian intuition;
- train, validation, and test separation; leakage; overfitting; underfitting; and class imbalance;
- confusion-matrix terms, accuracy, precision, recall, F1, ROC-AUC, and PR-AUC.

The fraud-metrics lesson includes an imbalanced dataset where a model that always predicts “not fraud” obtains approximately 99.9% accuracy while providing zero fraud recall. The exercise requires the student to explain and calculate the useful metrics rather than accept accuracy alone.

Notebooks are Colab-compatible: they use repository-relative data paths with a documented upload fallback and avoid environment-specific PyCharm APIs. Stored outputs remain small and deterministic.

## 8. Progressive project: Banking AI Lab

`projects/banking_ai_lab` is an importable package that develops through seven documented stages:

1. parse and validate transaction CSV rows;
2. generate analytics and JSON reports;
3. analyze transactions with Pandas and NumPy;
4. expose selected operations through FastAPI;
5. persist transactions in PostgreSQL with SQLAlchemy;
6. add API and database integration tests;
7. perform exploratory analysis in a Jupyter notebook.

The canonical transaction fields are `id`, `user_id`, `amount`, `currency`, `merchant`, `category`, `timestamp`, `status`, and `is_fraud`. `is_fraud` is a synthetic boolean fraud label used only by generated learning data. Money is represented as decimal values at domain and persistence boundaries. Timestamps are timezone-aware. Dataset generation uses a fixed seed and synthetic identities only.

Each stage has its own acceptance criteria and test command. Starter boundaries stay unimplemented when implementing them would solve the student task. Supporting infrastructure—configuration parsing, application factories, fixtures, and test helpers—may be complete when it teaches setup rather than the target algorithm.

## 9. Synthetic datasets

The repository contains a small deterministic CSV suitable for Git plus a generation script. It includes realistic currencies, merchants, categories, statuses, repeated users, occasional duplicates, missing optional business values, and a rare synthetic fraud label for metrics lessons. No row represents a real person or financial account.

The generation command reproduces the checked-in file byte-for-byte under the documented Python and dependency versions. Generated reports, databases, notebook checkpoints, and large derived files are ignored by Git.

## 10. Exercise test behavior

`uv run pytest` is a repository health check and exits successfully on the untouched starter repository.

Exercise tests call starter boundaries through a small helper. The helper converts only `NotImplementedError` from an untouched boundary into pytest's expected-incomplete outcome. This gives three meaningful states:

- untouched boundary: expected-incomplete test;
- incorrect attempted implementation: failed test;
- correct implementation: passed test.

No broad exception is swallowed. Import errors, syntax errors, unexpected exceptions, failed assertions, and regressions fail normally. The test summary displays expected-incomplete cases so the repository never implies that exercises are already solved.

Supported commands include:

```powershell
uv run pytest
uv run pytest modules/01_python_core
uv run python scripts/learn.py list
uv run python scripts/learn.py status
uv run python scripts/learn.py test python-collections
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

`scripts/learn.py` reads `curriculum.toml`, validates known lesson and exercise identifiers, and delegates test execution without modifying tracked files. `progress.md` remains a manually edited checklist.

## 11. Python project and dependency policy

- Minimum Python version: 3.12.
- Project management: `uv` with a committed lock file.
- Runtime libraries: FastAPI, Pydantic, Pydantic Settings, SQLAlchemy, PostgreSQL driver, NumPy, and Pandas.
- Development libraries: pytest, pytest-asyncio, HTTPX2, Ruff, mypy, JupyterLab, and notebook support required by the checked-in notebooks.
- Packaging: standard `pyproject.toml` with a small `src/roadmap_tools` package.
- Formatting and linting: Ruff.
- Static type checking: mypy over repository tooling, runnable examples, backend code, and typed starter modules. Notebook cells and intentionally broken debugging inputs are excluded explicitly.

Dependencies are kept at the root. No Poetry, Conda, Pipenv, Hatch, or Java-style multi-module build is introduced.

## 12. Error handling and student feedback

- Setup validation reports the detected Python version, `uv` availability, virtual environment path, and next corrective command.
- The learning CLI reports unknown identifiers and lists close valid choices.
- Exercise instructions identify the exact file the student edits and the exact command that verifies it.
- Intentional broken-code tasks live in non-imported fixture files so they cannot break collection of the health suite.
- PostgreSQL-dependent checks skip with an actionable reason when their opt-in environment variable is absent.
- Notebook examples fail visibly on missing required columns or invalid dtypes rather than silently coercing every value.

## 13. Documentation and PyCharm workflow

The root README describes the audience, roadmap, current scope, learning rules, Banking AI Lab evolution, and all primary commands. `docs/setup.md` provides Windows-first setup:

1. install Python 3.12+ and `uv`;
2. run `uv sync --all-groups`;
3. select `.venv\Scripts\python.exe` as the PyCharm interpreter;
4. mark the repository root as the working directory;
5. run the environment validation and health test;
6. start the first lesson.

The Java-to-Python cheat sheet maps records, interfaces, streams, nullable values, test frameworks, build metadata, DTO validation, resource management, and concurrency concepts while explicitly describing non-equivalence.

## 14. Git and repository hygiene

The repository excludes virtual environments, IDE metadata, caches, coverage data, local databases, environment files, secrets, generated reports, notebook checkpoints, and large derived datasets. An `.env.example` is included only where Module 02 introduces configuration.

The initial implementation is committed in logical groups after verification. No remote, push, or pull request is created without a later user request.

## 15. Verification and acceptance criteria

The repository is ready when all of the following are demonstrated from the repository root:

1. `uv sync --all-groups` succeeds on a supported Python installation.
2. `uv run pytest` exits zero and reports untouched student boundaries as expected-incomplete rather than passed.
3. A controlled incorrect implementation produces a failing exercise test, and restoring the starter restores the health result.
4. A temporary correct implementation of one representative exercise produces a passed test, then is removed before delivery.
5. `uv run ruff check .` exits zero.
6. `uv run ruff format --check .` exits zero.
7. `uv run mypy` exits zero for the configured scope.
8. Every identifier exposed by `scripts/learn.py list` resolves to an existing README and test target.
9. The dataset generation check proves deterministic output.
10. FastAPI smoke tests exercise application startup, validation, and a health endpoint without PostgreSQL.
11. PostgreSQL tests remain opt-in and explain their prerequisite when skipped.
12. Checked-in notebooks parse successfully and execute the documented introductory cells against the synthetic dataset.
13. The root README's tree, commands, paths, and first-lesson link match the actual repository.
14. No exercise solution is present in the normal working tree.

## 16. Delivery report

The final handoff identifies:

- the repository structure;
- implemented curriculum and tooling;
- the PyCharm opening procedure;
- the exact first command: `uv sync --all-groups`;
- the exact first lesson: `modules/01_python_core/00_environment/README.md`;
- the starter files the student is expected to implement;
- verification results with command counts and any intentionally skipped integration checks.
