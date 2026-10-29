# Текущая учебная карта: Java/Spring → Python → ML Engineer

Это действующая точка входа в программу. Старые планы `superpowers/plans`, wave
reports и отчёты проверок описывают состояние на свою дату. Они не переопределяют
этот маршрут и не означают, что ученик выполнил работу. Актуальный состав берётся
из `curriculum.toml`, обязательные ID маршрута — из `learning_tracks.toml`.

```powershell
uv sync --locked
uv run python scripts/learn.py inventory
uv run python scripts/learn.py track ml-engineer
uv run python scripts/learn.py track applied-ai
uv run python scripts/learn.py track applied-nlp
```

## Как пользоваться

У тебя уже есть инженерная база Java/Spring. Не требуется повторять общий курс
программирования, но нужно руками освоить другую семантику Python, работу с
массивами/таблицами и принятие решений при неопределённости. Чтение теории,
запуск чужого demo, самостоятельное решение и защита — четыре разные действия.

Для каждого этапа: прочитать theory/README → предсказать результат примера →
запустить demo → решить starter без копирования → `check ID` → ответить на
вопросы и перенести приём на другой вход. Возвращаться к prerequisite нормально.
`test ID` допускает незаполненные задания; `check ID` их не засчитывает.

## Общее основание и обязательная практика

| Этап | Prerequisites | Теория и примеры | Обязательный результат / оценка | Куда дальше |
|---|---|---|---|---|
| 1. Python core | Опыт программирования; [setup](setup.md) | [Модуль 01](../modules/01_python_core/README.md), [Java/Python](java-to-python-cheatsheet.md) | Исходные упражнения модуля; объяснить mutability, scope, iterators, exceptions, types и tests | Async и доставка пакета |
| 2. Жизненный цикл async | Functions, exceptions, context managers, базовый asyncio | [Async lifecycle](../modules/01_python_core/exercises/async_lifecycle/README.md) и [теория](../modules/01_python_core/10_asyncio/theory.md) | `python-async-lifecycle`: ограничение конкурентности, sibling failure, external cancellation и cleanup | Async API и сетевые нагрузки |
| 3. Python package | Modules/imports, typing, тесты, I/O | [Package delivery](../modules/01_python_core/exercises/package_delivery/README.md) | `python-package-delivery`: wheel в чистом окружении, запуск вне checkout, общий transform train/serve | Backend и model artifact |
| 4. Backend и данные в БД | Этапы 1–3; существующие знания HTTP/SQL | [Модуль 02](../modules/02_python_backend/README.md), [Alembic](../modules/02_python_backend/exercises/schema_migrations/README.md) | Исходная API/SQL практика; `backend-schema-migrations`: заполненная схема, backfill, downgrade, сохранение данных | Data foundations |
| 5. Данные и статистика | Python + SQL | [Модуль 03](../modules/03_data_foundations/README.md), paired comparison и experiment design | Пропуски/дубликаты/joins, feature availability, group/time splits, метрики и неопределённость; исходные check ID | Механика моделей |
| 6. ML-процесс | Этап 5; NumPy/Pandas | [Модуль 04](../modules/04_machine_learning/README.md) | Постановка, Dummy baseline, train-only preprocessing, validation, model selection, calibration/error slices, воспроизводимость | Математическая практика и внешний проект |
| 7. Градиенты | Линейная модель, производная суммы/композиции, NumPy | [MSE/BCE и L2](../modules/04_machine_learning/exercises/gradient_derivations/README.md) | `ml-gradient-derivations`: вывести w/b градиенты, проверить finite differences, обсудить редукцию и устойчивость | Training bridge/PyTorch |
| 8. Геометрия | Векторы, матрицы, скалярное произведение, этап 6 | [Rank/Ridge/PCA](../modules/04_machine_learning/exercises/linear_geometry/README.md) | `ml-linear-geometry`: коррелированные признаки, condition number, регуляризация, PCA по 2×2 covariance | Интерпретация preprocessing и регуляризации |
| 9. Деревья и boosting | Loss/validation и этап 6 | [Stump и residual boosting](../modules/04_machine_learning/exercises/tree_boosting/README.md) | `ml-tree-boosting`: выбрать split по вычислениям, пройти несколько boosting steps, сравнить train/dev | Tabular model comparison |
| 10. Устойчивость | Статистика, split, полный training pipeline | [Training stability](../modules/03_data_foundations/exercises/training_stability/README.md) | `data-training-stability`: полные retrains по seeds/sizes; отличить их вариативность от paired bootstrap фиксированных predictions | Независимый tabular проект |
| 11. Внешний tabular | Этапы 5–10, reproducibility | [External tabular](../projects/external_tabular/README.md) | `ml-external-tabular`: публичные данные, исходные файлы/hashes, split IDs, baseline/модели, неопределённость, ошибки, независимая защита | Pretrained NLP и deployment |
| 12. PyTorch и HF | Градиенты, training bridge, splits | [PyTorch](../labs/01_pytorch_foundations/README.md), [HF](../labs/02_huggingface_models/README.md), [compute guide](compute-guide.md) | Исходные lab checks и отдельные resume/diagnostics/attention продолжения; random-model mechanics ещё не external quality | Внешний текстовый проект |
| 13. Внешний текст | Этап 12, tabular experimental discipline | [External model study](../projects/document_intelligence_lab/external_model_study/README.md) | `document-external-model-study`: TF-IDF vs настоящий pretrained frozen encoder vs adapted encoder на одном внешнем split, реальные артефакты и защита | ML Engineer core завершает operational этап |
| 14. Pipeline и lifecycle | API, SQL, saved model, оба проекта | [Data pipeline](../projects/document_intelligence_lab/data_pipeline/README.md), [service lifecycle](../projects/document_intelligence_lab/production_readiness/README.md) | `ml-data-pipeline`, `production-service-lifecycle`: idempotency/late events, TCP load, timeout/restart/rollback, monitoring, один cloud design | Общая защита и подходящие вакансии |

Математика здесь встроена в моделирование. Если вывод непонятен, сначала разобрать
маленький числовой пример из theory, затем переписать формулу по индексам и только
потом переходить к векторному NumPy. Быстрый ответ autograd не заменяет эту проверку.

## Applied AI: дополнительный маршрут

`applied-ai` включает ML-основание и затем модули 05 → 06 → 07 → 08.
Это расширение подготовки, а не требование владеть всеми AI-специализациями для
любой ML-вакансии. Используй его, если хочешь строить LLM-приложения и RAG.

| Переход | Что изучить | Что предъявить |
|---|---|---|
| ML/text → LLM contracts | [Модуль 05](../modules/05_llm_engineering/README.md) | Prompt/context/structured output, retry и независимая оценка, исходные упражнения |
| LLM → retrieval | [Модуль 06](../modules/06_rag/README.md) и [real RAG](../labs/03_real_rag/README.md) | Retrieval relevance отдельно от ответа; corpus/chunks/ACL/versioning |
| Retrieval → полный ответ | [End-to-end RAG](../labs/03_real_rag/end_to_end/README.md) | `rag-end-to-end-evaluation`: dense masked mean pooling + generator, dev/holdout и no-answer/ambiguous/stale/ACL случаи |
| RAG → bounded workflows | [Модуль 07](../modules/07_agents/README.md) | Ограничения tools/loops, checkpoints, approvals и измеримые traces |
| Application → эксплуатация | [Модуль 08](../modules/08_production_ai/README.md) | Reliability/budget/privacy/rollout, затем общий TCP lifecycle и ручная защита |

Оффлайн provider doubles проверяют wiring и политики. Для заявления о качестве
pretrained модели или RAG нужен реальный запуск с зафиксированными моделями,
данными и запросами; честно отрицательный результат допустим. Исторические
MiniLM CLS/Ollama smoke не заменяют новый heldout-эксперимент.

## Группы окружения и пределы локальной машины

Базовые упражнения используют CPU и не скачивают данные во время тестов.
Alembic подключается через `--group migrations`; PyTorch/HF — через `--group training`.
В [compute guide](compute-guide.md) показаны отдельные окружения и ограничения
памяти. Уменьшать batch/sequence length и использовать маленький encoder допустимо;
менять протокол оценки ради удобной метрики — нет. Full-scale LLM training не нужен.

Fine-tuning/LoRA, local MLflow/Qdrant и модельный serving уже имеют материалы:
[fine-tuning](../labs/04_llm_finetuning/README.md),
[serving](../labs/05_model_serving/README.md),
[lifecycle](../labs/06_ml_lifecycle/README.md),
[local runtimes](local-runtime-continuation.md).
Их наличие не означает, что каждый GPU, Docker или внешний cloud сценарий был
исполнен. Используй [актуальную запись проверок](ml-engineer-readiness-verification.md).
Реальный vLLM остаётся обязательным отложенным этапом Applied AI/NLP на Linux/WSL;
формальная сдача — `lab-vllm-measurements`. Native Windows не является serving runtime.

## Зачёт и выбор следующего шага

```powershell
uv run python scripts/learn.py check ml-gradient-derivations
uv run python scripts/learn.py check ml-external-tabular
uv run python scripts/learn.py check-track ml-engineer
```

Последняя команда закономерно не пройдёт в чистом шаблоне: упражнения и внешние
отчёты ещё предстоит сделать. `TECHNICAL CHECKS PASSED` не меняет ручной progress
и не отменяет [защиту](readiness-assessment.md). Сначала закрывай конкретный ID;
общий check-track полезен перед итоговой защитой.

После core выбирай следующий блок по [вакансиям](job-market-comparison-2026-10-29.md).
Time series, recommender systems, computer vision, distributed data processing,
Kubernetes и глубокая research-математика — дальнейшие специализации. Их не нужно
все проходить до первых интервью. Прежний [Banking AI Lab](../projects/banking_ai_lab/README.md)
остаётся практикой Python/backend/data; два внешних проекта проверяют перенос
на новые данные и независимые решения.

## Углубление прикладных инструментов PA1

[Карта 11 новых практикумов](applied-tools-practice.md) расширяет NumPy/Pandas/sklearn,
PyTorch/HF, SFT/LoRA, NER, retrieval и управление экспериментами. Новый `applied-nlp`
маршрут фокусируется на текстах, документах и адаптации моделей.
Это следующий слой над описанным основанием; все learner TODO остаются самостоятельными.
