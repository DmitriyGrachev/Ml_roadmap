# Roadmap

This roadmap develops an experienced Java and Spring engineer's Python and AI engineering skills
through active work rather than broad survey material.
The first implemented learning wave covers Modules 01–03, extended by complete Modules 04–08.
The full roadmap now contains 57 lessons and two model labs. Work through the exercises yourself; offline simulations
are learning tools, not evidence of live model performance or production readiness.

## Связная карта первой модельной волны

Не требуется сначала пройти все восемь модулей. Общая база: Python collections,
functions, typing, I/O, testing → NumPy/data quality/split → problem framing,
preprocessing, regression и evaluation → [короткий мост](../modules/04_machine_learning/07_training_bridge/README.md).
Существующие задания остаются prerequisites, не продублированы в labs.

| Маршрут | Порядок после общей базы | Приоритет / готовность |
| --- | --- | --- |
| Applied AI | [PyTorch foundations](../labs/01_pytorch_foundations/README.md) → [HF models](../labs/02_huggingface_models/README.md) → modules05/06 → real RAG → bounded workflows → deployment | первые две labs CORE/READY; offline verification отдельно; real RAG/deployment PLANNED |
| ML Engineering | PyTorch → HF + небольшой encoder adaptation → experiments → SFT/LoRA → lifecycle | PyTorch/HF CORE, adaptation ML-DEPTH; tracking/SFT/lifecycle PLANNED |
| Backend/API | module02 можно проходить параллельно с data/ML | CORE для serving, не блокирует первое обучение модели |

READY означает, что инструкции и незаполненные контракты подготовлены.
VERIFIED применяется только с [записью среды, команд и границ](wave1-verification.md).
Ни один статус материалов не означает выполненный вами урок. Приоритет и готовность
— разные оси. [Следующие этапы и специализации](ai-ml-extension-plan.md).

[Аудит пяти направлений после первой волны](roadmap-coverage-review.md) уточняет
покрытие tabular ML, calibration/interpretation, training resume, memory-aware data
и system design: существующие материалы, конкретные пробелы и по одному PLANNED
продолжению с критериями освоения. Первая волна остаётся завершённой; эти продолжения
не добавляют новых обязательных prerequisites к уже подготовленным labs.

## Wave 2 — углубление и самостоятельная практика

[Карта фактического покрытия](wave2-coverage.md) перечисляет 14 новых exercise ID
с точными README/prerequisites. Каталог: 162 материала, включая 102 exercises,
57 lessons, две labs и один project. Материалы READY; свежие результаты технической
проверки — в [журнале](wave2-verification.md). TODO ученика не выполнены,
его эксперименты NOT_RUN, содержательная защита REQUIRES_REVIEW.

После общей базы: `data-paired-model-comparison` → `data-randomized-experiment`;
затем `ml-knn-mechanics` и `ml-tabular-study` (со своими ML prerequisites).
После базовых labs: `lab-training-resume`, `lab-training-diagnostics`,
`lab-attention-mechanics`; эти продолжения не расширяют старый `check lab-*`.

Четыре открытых контроля: `data-release-study` после Python I/O/testing/data quality;
`ml-evaluation-case` после tabular/validation; `lab-training-diagnostics` после
PyTorch/gradient bridge; `production-product-study` после framing/evaluation/serving/rollout.
Для каждого нужны собственные наблюдения и [ручная защита](project-defense.md),
а не только JSON с полями или зелёный smoke.

Боковые ветки: `rag-ranking-study` после retrieval metrics/fusion/paired comparison,
перед будущим real RAG; `ml-forecasting-intro` после temporal split и ML evaluation.
`python-interview-patterns` и `backend-analytics-sql` проходят параллельно после
своих Python/SQL prerequisites. Полные ranking/recommendations/time-series
специализации остаются PLANNED. Выбирайте exercise через `list`/README;
ручной progress по прежним урокам и labs сохранён.

## Существующие модули (пути и порядок сохранены)

1. **Module 01 — Python core:** native Python object semantics, collections, functions, typing, data modeling, I/O, generators, decorators, testing, and async I/O.
2. **Module 02 — Production Python and FastAPI:** API composition, Pydantic models, dependencies, observability, SQLAlchemy, PostgreSQL boundaries, testing, and delivery.
3. **Module 03 — Data foundations:** NumPy, Pandas, data quality, practical statistics, leakage-aware splits, and fraud metrics.
4. **Module 04 — Machine Learning:** [seven lessons](../modules/04_machine_learning/README.md) on problem framing, validation, preprocessing, model selection, evaluation, reproducibility, and the small bridge to model training.
5. **Module 05 — LLM Engineering:** [six lessons](../modules/05_llm_engineering/README.md) on provider interfaces, prompt contracts, structured outputs, context budgets, evaluation, and bounded retries/tools.
6. **Module 06 — Retrieval-Augmented Generation:** [six lessons](../modules/06_rag/README.md) on retrieval contracts, ingestion and chunking, lexical/dense search, hybrid ranking, citation checks, and retrieval/answer evaluation.
7. **Module 07 — Agents and workflows:** [six lessons](../modules/07_agents/README.md) on state, permission-controlled tools, bounded loops, checkpoints and approval, LangGraph/MCP, and trace evaluation.
8. **Module 08 — Production AI / LLMOps:** [six lessons](../modules/08_production_ai/README.md) on serving contracts, release gates, observability, budgets and resilience, privacy, and rollout/incident decisions.

For practice outside the banking domain, follow the [neutral Medium practice map](neutral-practice.md).
The tasks cover calendars, libraries, weather, park visits, museum events, documents, workflows,
and service operations. Read each task's prerequisites before jumping ahead.

## Advanced sequence

After Module 05, follow 06 → 07 → 08. First establish what information a retrieval system may
return and how to measure it. Then build bounded workflows around explicit state, tools and human
authority. Finally define release criteria and operational safeguards. Each of these three modules
contains six runnable lesson examples; RAG and Production AI now have nine exercises each,
and Agents has eight, including each module's original standalone Medium task
and three additional neutral exercises. Across all eight modules, 24 new standalone tasks add
practice without replacing existing exercises or changing the lesson sequence.

No required lesson calls a paid model, downloads embeddings, deploys a cloud resource, or needs a
vector database. Local framework examples use the locked dependencies. Optional live extensions
require separate credentials, provider documentation, representative data and operational review.

## Banking AI Lab

One synthetic-data project links the modules without hiding the learning goal behind framework ceremony. It progresses through CSV parsing and validation, analytics and JSON reporting, NumPy/Pandas analysis, FastAPI operations, PostgreSQL persistence, integration tests, and exploratory notebooks. Money stays decimal at domain and persistence boundaries; timestamps are timezone-aware.

## Start and track

Follow the [Windows and PyCharm setup](setup.md), then begin with
[Environment and workflow](../modules/01_python_core/00_environment/README.md). Update the manual
[progress checklist](../progress.md) as lessons are completed.
