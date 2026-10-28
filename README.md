# AI Engineer Roadmap

An active-learning roadmap for an experienced Java and Spring backend engineer moving into Applied AI and AI Engineering. It combines concise lessons, starter exercises with automated feedback, realistic mini-features, and a progressive Banking AI Lab portfolio project.

## Current scope

The foundation, learning workflow, all eight modules, and the progressive Banking AI Lab are ready.
Modules 01–08 are implemented, with 57 lessons, 102 exercises, and one progressive project.
Two model-training labs extend that foundation; later labs are explicitly PLANNED.
All eight modules include neutral-theme Medium practice. Implemented courseware includes examples
and deliberately unsolved student tasks; it does not mean those tasks are already completed.

New: [RAG and evaluation](modules/06_rag/README.md),
[Agents, workflows and MCP](modules/07_agents/README.md), and
[Production AI / LLMOps](modules/08_production_ai/README.md).
For practice outside banking, use the [neutral practice map](docs/neutral-practice.md).
It includes 24 additional exercises, three per module, with separate starters and automated tests.
Existing tasks and their contracts are unchanged.

Start with the first lesson: [Environment and workflow](modules/01_python_core/00_environment/README.md).

Continue with [Object Model](modules/01_python_core/01_object_model/README.md), then
[Collections](modules/01_python_core/02_collections/README.md), before the first coding
exercise: [Detect duplicate transactions](modules/01_python_core/02_collections/exercises/detect_duplicates/README.md).

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
├── labs/
├── projects/banking_ai_lab/
├── projects/document_intelligence_lab/
├── datasets/
├── scripts/
├── src/roadmap_tools/
└── tests/integration/
```

## Windows-first start

Open PowerShell at the repository root (for example, `C:\path\to\AIML\_road`), then synchronize the single project environment:

```powershell
uv sync --locked
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
uv sync --locked
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

## Первая модельная волна

Существующие 56 уроков и 88 упражнений сохранены. Новое: короткий
[мост NumPy → обучение](modules/04_machine_learning/07_training_bridge/README.md),
[PyTorch lifecycle](labs/01_pytorch_foundations/README.md) и
[Hugging Face](labs/02_huggingface_models/README.md).
Читайте [связный маршрут](docs/roadmap.md), [аудит](docs/skills-matrix.md),
[ресурсы и PyCharm](docs/compute-guide.md), [реальные результаты проверок](docs/wave1-verification.md).

`test` проверяет инфраструктуру и допускает незавершённые `xfail`.
`check` — строгий зачёт только выбранного материала: обязательные skips/xfails,
ошибки, пустая collection и отсутствующие обязательные результаты не дают зачёт.
Он не решает задания и не меняет ваш progress.

```powershell
uv run python scripts/learn.py check python-word-index
uv run python scripts/learn.py check ml-training-bridge
uv sync --locked --group training
uv run --group training python -m labs.01_pytorch_foundations.example
uv run --group training python scripts/learn.py check lab-pytorch
uv run --group training python -m labs.02_huggingface_models.example
uv run --group training python scripts/learn.py check lab-huggingface
```

Нетронутые student TODO и отсутствующие ученические отчёты означают ненулевой
`check` — это ожидаемо, а не поломка установки. Offline smoke не доказывает качество
настоящей модели. Model/data downloads — только ваша отдельная явная команда.
[Продолжения R03–R11](docs/superpowers/plans/2026-10-11-remaining-roadmap.md)
теперь включают локальные демонстрации, тесты и самостоятельные вариации.
Это не завершённые учеником labs. Настоящие локальные MLflow registry, Qdrant и
PEFT теперь имеют отдельные авторские runtime-опыты без скачивания моделей:
[команды, результаты и ограничения](docs/local-runtime-continuation.md).
Pretrained quality, cloud и hosted CI не проверены; vLLM отложен по вашему решению
до появления Linux/WSL. [Предыдущие offline проверки](docs/remaining-roadmap-verification.md).

## Вторая волна: практика и самостоятельные контроли

Во второй волне добавлены 14 exercise ID; после отдельного A1-практикума текущий
каталог содержит 163 материала (57 lessons, 103 exercises, 2 labs, 1 project).
[Карта второй волны](docs/wave2-coverage.md) даёт ссылки и
prerequisites для каждого нового задания; [порядок прохождения](docs/roadmap.md)
связывает статистику, kNN/tabular, продолжения PyTorch/HF и четыре открытых контроля.
Ranking и forecasting — короткие боковые ветки; глубокие специализации PLANNED.
Материалы READY; [проверенные команды и ограничения](docs/wave2-verification.md)
относятся к инфраструктуре. Реализации ученика остаются TODO, его эксперименты
NOT_RUN, содержательная защита REQUIRES_REVIEW. Новые упражнения выбираются через
`list` и README; прежний ручной progress с уроками/labs не расширен.

```powershell
.venv/Scripts/python.exe scripts/learn.py list
.venv/Scripts/python.exe scripts/learn.py test data-paired-model-comparison
.venv/Scripts/python.exe scripts/learn.py check data-paired-model-comparison
```

Последний `check` станет успешным только после вашей реализации. Три продолжения
labs требуют [отдельного training interpreter](docs/compute-guide.md).

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
