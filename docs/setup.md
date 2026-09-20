# Windows and PyCharm setup

## 1. Install prerequisites

Install Python 3.12 or newer and `uv` on Windows. Open PowerShell in the repository root (for example, `C:\path\to\AIML\_road`); commands in this guide assume that working directory.

## 2. Create the shared environment

```powershell
uv sync --all-groups
```

This creates the one repository environment at `.venv`. Do not create a second environment per module.

## 3. Open the project in PyCharm

Open the repository directory in PyCharm. In the project interpreter settings, choose the existing interpreter at `.venv\Scripts\python.exe`. For every run configuration, set the working directory to the repository root rather than an individual lesson folder.

## 4. Validate and test the repository

```powershell
uv run python scripts/learn.py validate-env
uv run pytest
```

The untouched exercise helper reports an expected-incomplete result. That is an intentional learner-facing state, not a solved exercise or a suppressed test failure.

## 5. Start the roadmap

The first lesson is [Environment and workflow](../modules/01_python_core/00_environment/README.md).
The first coding exercise is
[Detect duplicate transactions](../modules/01_python_core/02_collections/exercises/detect_duplicates/README.md).

List the implemented catalog entries with `uv run python scripts/learn.py list`, run an item's tests
with `uv run python scripts/learn.py test python-collections`, and review the manual checklist with
`uv run python scripts/learn.py status`.

## Useful checks

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Return to the [repository overview](../README.md) for the workflow and roadmap.
