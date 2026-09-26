# Neutral practice

Every module has at least one **Medium** exercise outside the banking domain. Medium means
combining several concepts, validating inputs, and handling edge cases rather than implementing
a single expression. These tasks complement, not replace, the ordered lessons.

| Module | Suggested exercise | What you practise | Catalog ID |
| --- | --- | --- | --- |
| 01 — Python core | [Merge calendar intervals](../modules/01_python_core/exercises/calendar_intervals/README.md) | Sorting, immutable inputs, interval boundaries | `python-calendar-intervals` |
| 02 — Python backend | [Search a library catalog](../modules/02_python_backend/exercises/library_search/README.md) | Request validation, filtering, stable pagination | `backend-library-search` |
| 03 — Data foundations | [Summarize weather observations](../modules/03_data_foundations/exercises/weather_quality/README.md) | Data quality and grouped summaries | `data-weather-quality` |
| 04 — Machine Learning | [Mixed-feature park-visit pipeline](../modules/04_machine_learning/03_preprocessing/exercises/mixed_feature_pipeline/README.md) | Imputation, encoding, train-only fitting | `ml-mixed-feature-pipeline` |
| 05 — LLM Engineering | [Museum event contract](../modules/05_llm_engineering/03_structured_outputs/exercises/event_contract/README.md) | Structured output and semantic validation | `llm-event-contract` |
| 06 — RAG | [Chunk documents with overlap](../modules/06_rag/exercises/text_chunking/README.md) | Chunk boundaries, overlap and source metadata | `rag-text-chunking` |
| 07 — Agents | [Schedule a bounded workflow](../modules/07_agents/exercises/workflow_schedule/README.md) | Dependencies, deterministic order and stop conditions | `agents-workflow-schedule` |
| 08 — Production AI | [Report request reliability and latency](../modules/08_production_ai/exercises/request_metrics/README.md) | Availability, latency and operational summaries | `production-request-metrics` |

Modules 04 and 05 contain additional neutral Medium exercises: see their
[ML practice map](../modules/04_machine_learning/README.md) and
[LLM practice map](../modules/05_llm_engineering/README.md).
Modules 06–08 now also contain complete six-lesson sequences and four additional Medium exercises
each. Follow the [RAG practice map](../modules/06_rag/README.md),
[agent practice map](../modules/07_agents/README.md), and
[production practice map](../modules/08_production_ai/README.md) for the complete progression.
The original standalone tasks above remain at their existing paths, with their contracts unchanged.

## Additional neutral practice — 24 new exercises

These are new, independent tasks, not replacements or renamed versions of the existing exercises.
Each has its own README, typed `starter.py`, and behavioral `test_starter.py`.
Start with the Beginner word index after the collections lesson; the remaining additions are
Medium and list their prerequisites. API, database, data and AI exercises all run locally.

| Module | Three additional exercises |
| --- | --- |
| 01 — Python | [Word index](../modules/01_python_core/exercises/word_index/README.md); [lazy stream pages](../modules/01_python_core/exercises/paged_stream/README.md); [bounded async fetching](../modules/01_python_core/exercises/bounded_fetch/README.md) |
| 02 — Backend | [Room booking API](../modules/02_python_backend/exercises/room_booking_api/README.md); [conditional document cache](../modules/02_python_backend/exercises/conditional_cache/README.md); [equipment repository](../modules/02_python_backend/exercises/equipment_repository/README.md) |
| 03 — Data | [Image block pooling](../modules/03_data_foundations/exercises/image_pooling/README.md); [library loan joins](../modules/03_data_foundations/exercises/library_joins/README.md); [paired observations](../modules/03_data_foundations/exercises/paired_observations/README.md) |
| 04 — ML | [Chronological weather split](../modules/04_machine_learning/exercises/time_series_split/README.md); [wildlife classification report](../modules/04_machine_learning/exercises/multiclass_report/README.md); [weather-alert threshold](../modules/04_machine_learning/exercises/threshold_policy/README.md) |
| 05 — LLM | [Priority context packing](../modules/05_llm_engineering/exercises/context_packing/README.md); [versioned response cache](../modules/05_llm_engineering/exercises/response_cache/README.md); [answer stream assembly](../modules/05_llm_engineering/exercises/stream_assembly/README.md) |
| 06 — RAG | [Index refresh plan](../modules/06_rag/exercises/index_sync/README.md); [evidence diversity](../modules/06_rag/exercises/context_diversity/README.md); [retrieval regression guard](../modules/06_rag/exercises/retrieval_regression/README.md) |
| 07 — Agents | [Tool plan validation](../modules/07_agents/exercises/plan_validation/README.md); [permission-filtered handoff](../modules/07_agents/exercises/handoff_packet/README.md); [tool result routing](../modules/07_agents/exercises/tool_result_routing/README.md) |
| 08 — Production | [Artifact manifest](../modules/08_production_ai/exercises/artifact_manifest/README.md); [service error budget](../modules/08_production_ai/exercises/error_budget/README.md); [record retention plan](../modules/08_production_ai/exercises/retention_policy/README.md) |

Use the focused pytest command in each README, or its catalog ID:

```powershell
uv run python scripts/learn.py test python-word-index
uv run python scripts/learn.py test data-image-pooling
uv run python scripts/learn.py test agents-plan-validation
```

The artifact and retention tasks only inspect or plan: they do not execute model artifacts,
delete files, deploy services, or claim to replace live infrastructure validation.

## How to work

1. Read the task README, including prerequisites, input/output rules, and invalid-input behavior.
2. Open the adjacent `starter.py` and implement its `TODO` boundary. Keep test expectations intact.
3. Run the task by its catalog ID from the repository root:

   ```powershell
   uv run python scripts/learn.py test python-calendar-intervals
   uv run python scripts/learn.py test ml-mixed-feature-pipeline
   uv run python scripts/learn.py test llm-event-contract
   ```

4. An untouched boundary reports `XFAIL` (not implemented); it is not a solved task.
   After implementing it, the behavioral tests should pass without expected failures.
5. Explain your choices and edge cases before moving on. Lesson completion is tracked manually in
   [progress.md](../progress.md); the checklist does not auto-complete standalone exercises.

Use the focused exercise command while learning. The global repository checks also verify the
distributed *unsolved* starter template, so their starter-hygiene assertions are maintainer checks,
not the acceptance criterion for your completed answers. See the [testing guide](testing-exercises.md).

All listed tasks are local and deterministic. No personal data, API credentials, paid model calls,
or model downloads are required. LLM fakes validate application contracts, not real model quality.
