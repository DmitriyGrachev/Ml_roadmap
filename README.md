# AI Engineer Roadmap

An active-learning roadmap for an experienced Java and Spring backend engineer moving into Applied AI and AI Engineering. It combines concise lessons, starter exercises with automated feedback, realistic mini-features, and a progressive Banking AI Lab portfolio project.

## Current scope

The foundation and learning workflow are ready. Modules 01–03 are planned next; their lesson folders are not present yet. Modules 04–08 are roadmap placeholders, not implemented courses.

Use the planned first lesson path as inline code: `modules/01_python_core/00_environment/README.md`.

Use the planned first coding path as inline code: `modules/01_python_core/02_collections/exercises/detect_duplicates/README.md`.

## Windows-first start

Open PowerShell at the repository root (for example, `C:\path\to\AIML\_road`), then synchronize the single project environment:

```powershell
uv sync --all-groups
```

In PyCharm, open this repository, select `.venv\Scripts\python.exe` as the project interpreter, and set the repository root as the working directory for run configurations. Validate the environment before starting a lesson:

```powershell
uv run python scripts/learn.py validate-env
```

See [Windows and PyCharm setup](docs/setup.md) for the complete workflow.

## Learning workflow

Run these commands from the repository root. Some commands are the final interface contract for Modules 01–03 and become useful as those modules arrive.

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

`uv run pytest` is the repository health check. An untouched student boundary is reported as expected-incomplete rather than as a completed exercise. Scoped tests will be added beside each lesson; use the exact command named in that lesson's exercise README.

Progress is intentionally manual: edit the checklist in [progress.md](progress.md), then inspect it with `uv run python scripts/learn.py status`.

## Roadmap and project thread

The learning sequence moves from native Python, through production FastAPI and data foundations, to the later AI topics. The Banking AI Lab evolves from CSV validation and transaction reports into data analysis, an API, PostgreSQL persistence, integration tests, and exploratory notebooks.

- [Roadmap](docs/roadmap.md)
- [Learning rules](docs/learning-rules.md)
- [Exercise testing model](docs/testing-exercises.md)
- [Java-to-Python cheat sheet](docs/java-to-python-cheatsheet.md)
- [Module 04 — Machine Learning](modules/04_machine_learning/README.md)
- [Module 05 — LLM Engineering](modules/05_llm_engineering/README.md)
- [Module 06 — Retrieval-Augmented Generation](modules/06_rag/README.md)
- [Module 07 — Agents](modules/07_agents/README.md)
- [Module 08 — Production AI](modules/08_production_ai/README.md)

## Principles

Learn by changing starter code, keeping test expectations intact, and recording your own progress. Examples use synthetic banking, payment, support-ticket, document, and LLM-style data; no real customer or financial-account data belongs in this repository.

See [LICENSE](LICENSE) for the MIT license.
