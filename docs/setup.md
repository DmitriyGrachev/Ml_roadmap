# Windows and PyCharm setup

## 1. Install prerequisites

Install Python 3.12 or newer and `uv` on Windows. Open PowerShell in the repository root (for example, `C:\path\to\AIML\_road`); commands in this guide assume that working directory.

## 2. Create the shared environment

```powershell
uv sync --locked
```

This creates the base repository environment at `.venv`. No per-module environment is needed.
After updating the course, run the same command again: Module 04 uses scikit-learn, included in
the shared dependency lock. Module 05 uses offline provider doubles and needs no API key,
model download, or paid account.
Module 07 includes LangGraph and the MCP SDK in this same environment. Its demonstrations are
local: no external MCP server or model account is required. Module 08 simulates operational
policies and does not require cloud infrastructure. Dependency versions are pinned by `uv.lock`.
The local LangGraph example explicitly disables LangSmith tracing and needs no tracing account.

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

## Первая модельная волна

После необходимых Python/data уроков откройте [мост](../modules/04_machine_learning/07_training_bridge/README.md).
Для двух labs явно установите `uv sync --locked --group training` и используйте
`uv run --group training ...`. В группе только необходимые CPU PyTorch/HF packages;
обычный `uv sync` без них. Старое `--all-groups` теперь включает и training.
Веса и датасеты эта установка не загружает. Полные команды и ограничения —
в [compute guide](compute-guide.md). Существующие модели упражнений не решены за вас.
