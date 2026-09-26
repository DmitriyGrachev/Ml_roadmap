# AI Engineer Roadmap

An active-learning roadmap for an experienced Java and Spring backend engineer moving into Applied AI and AI Engineering. It combines concise lessons, starter exercises with automated feedback, realistic mini-features, and a progressive Banking AI Lab portfolio project.

## Current scope

The foundation, learning workflow, all eight modules, and the progressive Banking AI Lab are ready.
Modules 01–08 are implemented, with 56 lessons, 88 exercises, and one progressive project.
All eight modules include neutral-theme Medium practice. Implemented courseware includes examples
and deliberately unsolved student tasks; it does not mean those tasks are already completed.

New: [RAG and evaluation](modules/06_rag/README.md),
[Agents, workflows and MCP](modules/07_agents/README.md), and
[Production AI / LLMOps](modules/08_production_ai/README.md).
For practice outside banking, use the [neutral practice map](docs/neutral-practice.md).
It includes 24 additional exercises, three per module, with separate starters and automated tests.
Existing tasks and their contracts are unchanged.

Start with the first lesson: [Environment and workflow](modules/01_python_core/00_environment/README.md).

Then try the first coding exercise: [Detect duplicate transactions](modules/01_python_core/02_collections/exercises/detect_duplicates/README.md).

For a neutral Beginner alternative after learning collections, start with
[Build a word index](modules/01_python_core/exercises/word_index/README.md).

## Repository structure

```text
ai-engineer-roadmap/
├── modules/01_python_core/
├── modules/02_python_backend/
├── modules/03_data_foundations/
├── modules/04_machine_learning/
├── modules/05_llm_engineering/
├── modules/06_rag/
├── modules/07_agents/
├── modules/08_production_ai/
├── projects/banking_ai_lab/
├── datasets/
├── scripts/
├── src/roadmap_tools/
└── tests/integration/
```

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

Run these commands from the repository root. They are the supported workflow for the implemented
Modules 01–08 and Banking AI Lab.

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

`uv run pytest` is the repository health check. An untouched student boundary is reported as
expected-incomplete rather than as a completed exercise. Scoped tests live beside each lesson; use
the exact command named in that lesson's exercise README.

Progress is intentionally manual: edit the checklist in [progress.md](progress.md), then inspect it with `uv run python scripts/learn.py status`.

## Roadmap and project thread

The learning sequence moves from native Python, through FastAPI, data foundations and ML, to
LLM applications, retrieval, bounded agent workflows, and production operations. The Banking AI Lab
evolves through the foundational modules from CSV validation and transaction reports into data
analysis, an API, PostgreSQL persistence, integration tests, and exploratory notebooks. Advanced
modules use separate focused exercises; they do not silently add a completed AI feature to the lab.

- [Roadmap](docs/roadmap.md)
- [Learning rules](docs/learning-rules.md)
- [Exercise testing model](docs/testing-exercises.md)
- [Neutral practice in all eight modules](docs/neutral-practice.md)
- [Java-to-Python cheat sheet](docs/java-to-python-cheatsheet.md)
- [Module 04 — Machine Learning](modules/04_machine_learning/README.md)
- [Module 05 — LLM Engineering](modules/05_llm_engineering/README.md)
- [Module 06 — Retrieval-Augmented Generation](modules/06_rag/README.md)
- [Module 07 — Agents](modules/07_agents/README.md)
- [Module 08 — Production AI](modules/08_production_ai/README.md)

## Principles

Learn by changing starter code, keeping test expectations intact, and recording your own progress.
Examples use synthetic banking, payment, document, library, weather, and LLM-style data; no real
customer or financial-account data belongs here. ML uses local synthetic datasets; LLM applications
use offline doubles. LangGraph/MCP examples run locally. Production exercises simulate release,
budget, privacy and rollout policies; they do not deploy services or prove live model quality.

See [LICENSE](LICENSE) for the MIT license.
