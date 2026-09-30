# План развития: от общей базы к двум траекториям

Первая волна ограничена мостом, scoped strict check и двумя labs. [Аудит](skills-matrix.md)
объясняет, что уже было и почему старые NumPy/ML задания не переписаны.
Приоритет темы: CORE, ML-DEPTH, OPTIONAL. Готовность материалов: PLANNED, READY,
VERIFIED с конкретной средой и командами. Отдельно — ручной прогресс ученика.

## Первая волна

- CORE: математический мост, строгий зачёт, PyTorch lifecycle, HF tokenizer/model lifecycle.
- ML-DEPTH: небольшой ограниченный encoder adaptation, не LLM SFT/LoRA.
- Сохраняем 8 модулей, Banking AI Lab, старые IDs и starter contracts.
- Библиотеки моделей только в `training`; без tracking server и serving зависимостей.
- [Фактические проверки и ограничения](wave1-verification.md), [ресурсы](compute-guide.md).

## Следующие волны — всё ниже PLANNED

| Этап | Prerequisites | Expected artifacts | Done |
| --- | --- | --- | --- |
| Real embeddings + vector DB + RAG / CORE Applied AI | HF, модуль 06, permissions/citations | snapshot документов, постоянный Qdrant index, eval queries/relevance labels, retrieval и answer reports | измерены lexical/embedding/hybrid, update/delete/ACL/no-answer; источники ответов проверены человеком |
| Data pipeline и experiment tracking / CORE | split/manifest, две labs, SQL/CSV | воспроизводимый dataset release, annotation guide, MLflow runs и реально сохранённые artifacts | повторный запуск не дублирует данные; восстановление по version/hash; одинаковый preprocessing train/inference |
| SFT/PEFT LoRA, QLoRA / ML-DEPTH | обе labs, held-out evaluation, resource budget | SFT dataset/template, baseline/prompting comparison, adapter, fixed eval protocol | безопасный reload адаптера; независимая оценка улучшений/деградаций; совместимость QLoRA проверена отдельно |
| Serving + vLLM / CORE concepts, OPTIONAL vLLM | backend, HF inference; fine-tuning НЕ prerequisite | отдельный lock/environment, API, bounded load script, TTFT/throughput/error/memory report | streaming/cancellation/deadline/backpressure; cold/warm и ограничения документированы; небольшой smoke не benchmark |
| Drift/monitoring/lifecycle / CORE | модельный artifact, serving, module 08 | schema/version contract, deployment smoke/CI, runbook, drift examples, rollback | controlled promotion и rollback модели+preprocessing; различены data drift/concept drift и качество с метками |
| Document Intelligence Lab / CORE capstone | базовый ML/HF; RAG затем serving | постановка, classifiers, документация+retrieval, architecture note, learner reports | два независимых evaluation протокола; ограниченный workflow и защита решения на английском |

Подробные спецификации: [RAG](../labs/03_real_rag/README.md),
[fine-tuning](../labs/04_llm_finetuning/README.md),
[serving](../labs/05_model_serving/README.md),
[lifecycle](../labs/06_ml_lifecycle/README.md),
[нейтральный проект](../projects/document_intelligence_lab/README.md).
PLANNED не попадает в executable catalog и не создаёт ложный зачёт.

## Точечные продолжения существующих уроков — материалы READY

[Аудит пяти направлений](roadmap-coverage-review.md) фиксирует, что уже покрыто,
и одно продолжение для каждого пробела: ансамбли/один boosting и feature ablation;
calibration + threshold + интерпретация; диагностируемый training resume;
memory-aware data release; защита AI/ML system design.
Эти продолжения теперь подготовлены как 14 отдельных exercise ID второй волны:
[покрытие, ссылки и prerequisites](wave2-coverage.md), [фактические проверки](wave2-verification.md).
Ансамбли/calibration объединены в tabular study; data release и system design —
открытые контроли; resume и debugging имеют отдельные lab targets. Их READY
означает подготовленные материалы; learner TODO, NOT_RUN эксперименты и
REQUIRES_REVIEW защита не превращаются в выполненный progress.
Короткие ranking/forecasting intro тоже READY, но специализации ниже — будущая работа.

## Специализации после общей базы — OPTIONAL, PLANNED

- CV/multimodal: prerequisites PyTorch/images; проект OCR каталога; done — независимая
  оценка ошибок по типам изображений, latency и лицензированный датасет.
- Time series: temporal validation; прогноз экологических измерений; done — backtest
  против seasonal baseline без будущих признаков.
- Ranking/recommendations: retrieval/metrics; поиск по каталогу; done — фиксированная
  relevance-разметка, negative sampling protocol и offline/online trade-offs.
- ML platform: reproducible lifecycle; один deployment pipeline; done — восстанавливаемый
  artifact и rollback. Kubernetes/IaC/distributed training только при обоснованной потребности.

Программа не обещает грейд или трудоустройство и не требует всех специализаций.
Облачный этап: одно облако, object storage, identities/permissions, secrets, контейнер,
network boundary, logs, budget и удаление ресурсов. Платное развёртывание необязательно.

## Первичные источники (проверены 26.09.2026)

- [PyTorch learning lifecycle](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)
- [Reproducibility limitations](https://docs.pytorch.org/docs/stable/notes/randomness.html)
- [Transformers training](https://huggingface.co/docs/transformers/en/training)
- [Dependency groups](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups)
- [CPU PyTorch with uv](https://docs.astral.sh/uv/guides/integration/pytorch/)

Источники подтверждают API/подходы, а не запуск на нашем ноутбуке. Такой запуск
документируется только в журнале проверки. Senior-вакансии не задают обязательный
список навыков для начала учёбы.
