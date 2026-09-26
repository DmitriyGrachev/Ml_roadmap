# Roadmap

This roadmap develops an experienced Java and Spring engineer's Python and AI engineering skills
through active work rather than broad survey material.
The first implemented learning wave covers Modules 01–03, extended by complete Modules 04–08.
The full roadmap now contains 56 lessons. Work through the exercises yourself; offline simulations
are learning tools, not evidence of live model performance or production readiness.

## Learning sequence

1. **Module 01 — Python core:** native Python object semantics, collections, functions, typing, data modeling, I/O, generators, decorators, testing, and async I/O.
2. **Module 02 — Production Python and FastAPI:** API composition, Pydantic models, dependencies, observability, SQLAlchemy, PostgreSQL boundaries, testing, and delivery.
3. **Module 03 — Data foundations:** NumPy, Pandas, data quality, practical statistics, leakage-aware splits, and fraud metrics.
4. **Module 04 — Machine Learning:** [six lessons](../modules/04_machine_learning/README.md) on problem framing, validation, preprocessing, model selection, evaluation, and reproducibility.
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
contains six runnable examples and eight exercises, including its original standalone Medium task
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
