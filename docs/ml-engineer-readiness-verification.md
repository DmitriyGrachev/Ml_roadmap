# Проверка ветки ML Engineer readiness

Исходная ветка: `codex/ai-ml-wave1`, commit
`934b34bcaab5c0c241dfa820d807a9bb61e166c6`.
Новая ветка: `codex/ml-engineer-readiness`. Дата работы: 29.10.2026 по Бухаресту.

## Что именно проверяется

Авторские примеры и инструменты — работающий код. Стартовые задания и собственные
submission-артефакты ученика оставлены незаполненными. `XFAIL` в общем pytest
означает незавершённость, а не успех ученика. Строгий `check` обязан завершаться
ненулевым кодом на таком шаблоне. Содержательная защита остаётся REQUIRES_REVIEW.

Ниже зафиксированы результаты локальной интеграции. Они относятся к авторскому
коду и инфраструктуре курса; готовность ученика оценивается отдельно по
[рубрике](readiness-assessment.md).

## Среда и воспроизводимые команды

Python 3.12.14, Linux; base/dev с optional `migrations`; отдельное CPU-окружение
`training`. Версии закреплены `uv.lock`. Проверки обычного каталога offline;
модели и датасеты не скачиваются автоматически во время pytest.

```bash
uv sync --locked --group migrations
uv run --no-sync python -m pytest -q
uv run --no-sync python -m pytest --maintainer -m maintainer_only -q
uv run --no-sync python -m ruff check .
uv run --no-sync python -m ruff format --check .
uv run --no-sync python -m mypy
uv run --no-sync python scripts/learn.py inventory
uv run --no-sync python scripts/learn.py track ml-engineer
```

Training выполняется в отдельном окружении по [compute guide](compute-guide.md),
чтобы `uv sync` без группы не удалял нужные optional dependencies неожиданно.
Реальные TCP-тесты требуют возможности открыть loopback socket. В ограниченном
sandbox отсутствие такой возможности является ограничением среды, не метрикой
качества учебного сервиса.

## Результаты интеграции

Каталог содержит **180 элементов: 57 уроков, 118 упражнений, 2 лабораторных
раздела и 3 проекта**. Добавлены 12 новых ID. Все 168 исходных записей каталога
сохранены без изменения их данных; старый префикс `progress.md` сохранён,
новые строки не отмечены выполненными. В маршруте `ml-engineer` — 123 ID,
в расширенном `applied-ai` — 178 ID. Это состав программы, а не число
самостоятельно завершённых работ.

| Проверка | Наблюдаемый результат |
|---|---|
| Один полный интеграционный `pytest -q` | 1629 passed, 87 skipped, 1294 xfailed, 4 deselected; 3 failed; 97.99 s. Причины и точечное закрытие перечислены ниже. |
| Два упавших inventory/import контракта после исправления | 2 passed, 0.40 s; новые упражнения включены в точные списки, starter миграции действительно импортируется. |
| Упавший mypy gate с изолированным кэшем | 1 passed, 1.14 s; запускает обычный mypy по базовому каталогу и проверяет присутствие backend-кода. |
| Явный maintainer gate | 4 passed; 14 optional collection skips, 2999 deselected; 5.73 s. |
| Ruff и форматирование на интегрированном коде | All checks passed; 1165 files already formatted. |
| Training mypy: `-p labs -p projects.document_intelligence_lab` | Success: no issues found in 158 source files. |
| Каталог, маршруты и навигация | 25 целевых тестов passed; неизменность исходных записей и progress проверена отдельно. |

Полный прогон обнаружил два устаревших списка упражнений и INTERNAL ERROR
локального общего кэша mypy. В списки добавлены новые пути, сохранены проверки
точного состава, количества, уникальных ссылок и collision-safe импорта.
Helper ссылок теперь поддерживает переход из модуля в `docs`. Проверка mypy
повторена с отдельным кэшем. Отдельные проверки типов также выявили ошибки
аннотаций в новых тестах миграции и RAG; исправления прошли scoped review,
свои короткие тесты и соответствующие проверки типов.

По просьбе не повторять длительные процессы **второй полный локальный pytest
после этих исправлений не запускался**. Таблица сообщает полный checkpoint
и результаты точечных повторов, а не изображает их новым полным зелёным прогоном.
Оставшееся предупреждение Starlette/AnyIO относится к deprecated alias в
зависимости и не меняет результат тестов.

### Проверки новых блоков

Это отдельные диагностические прогоны разработки; их числа нельзя складывать
с итоговым pytest как дополнительные независимые тесты.

| Область | Выполненная проверка |
|---|---|
| Математика и устойчивость | 17 passed, 44 xfailed; четыре author demo; типы 24 файлов. |
| Async / wheel / Alembic | 15 passed, 20 xfailed; установка wheel в чистое окружение вне checkout; настоящие миграции заполненной SQLite. Регрессия закрытия соединений: 6 passed, 2 xfailed; исправление аннотаций: 2 passed. |
| Внешние ML-проекты | Core: 28 passed, 1 skipped, 2 xfailed; training: 29 passed, 2 xfailed. Semantic tokenizer regression: 7 passed без скачивания весов. |
| RAG | Offline-проверки wiring/policies; исправление согласованности receipts: 39 passed, 1 xfailed; trace/type regression: 6 passed. Tiny random-model pooling проверяет механику, не качество pretrained encoder. |
| Service lifecycle / SQL pipeline | После усиления learner gates: 35 passed, 1 skipped, 8 xfailed; проверки вызывают learner-функции, сопоставляют артефакты и сохраняют сведения о неудачном запуске. |

Источник UCI red wine проверен по официальному HTTPS: 1599 строк данных,
84199 байт, SHA-256
`4a402cf041b025d4566d954c3b9ba8635a3a8a01e039005d97d6a710278cf05e`.
Данные и обученные модели не добавлены в git. Это проверка доступности и
происхождения источника, а не выполненный за ученика ML-проект.

## Единственный реальный TCP-запуск

Авторский lifecycle был выполнен один раз: запуск A → restart A → переключение B
→ отказ запуска при неверном digest → восстановление A. На каждом из четырёх
работающих этапов отправлены 8 обычных запросов с concurrency 3: всего 32 успешных
warm-запроса. Медианы по этапам: 2.95 / 3.48 / 5.11 / 2.53 ms; максимумы:
4.42 / 4.67 / 7.33 / 4.01 ms. Это небольшой локальный smoke, не production p99.

Четыре запроса с невалидным входом дали 422. Четыре probes с коротким deadline
в этом запуске успели завершиться успешно: **наблюдаемых timeout — 0**.
Путь обработки timeout проверяется детерминированным отдельным тестом; успешный
probe не выдаётся за наблюдённый сетевой timeout. Плохой digest завершил child
с кодом 3; работающие дочерние процессы были убраны, восстановленная identity A
совпала с исходной, предсказания A и B различались.

После этого transport был выделен в отдельный модуль, усилены learner/evidence
checks и сохранение неуспешного отчёта. Эти изменения проверены offline; TCP
эксперимент не повторялся. Приведённые timings относятся к одному более раннему
авторскому запуску и не являются benchmark окончательного commit.

## GitHub CI

Workflow проверяет base + migrations на Ubuntu и Windows; отдельный Windows job
проверяет training-код offline. Local-runtimes остаётся явным opt-in.
На момент фиксации локальной записи результат CI нового commit ещё отсутствовал;
текущий статус нужно читать в
[Actions для этой ветки](https://github.com/DmitriyGrachev/Ml_roadmap/actions?query=branch%3Acodex%2Fml-engineer-readiness).
Локальный Linux-результат не выдаётся за выполненный Windows job.

Публикуется новая ветка от указанного исходного commit. Исходные ветки не
обновляются. Draft PR не создаётся: workflow запускается и на push, и на PR,
поэтому для просмотра достаточно
[сравнения веток](https://github.com/DmitriyGrachev/Ml_roadmap/compare/codex/ai-ml-wave1...codex/ml-engineer-readiness)
без второго автоматического прогона.

## Проверенные регрессии

- CLI раньше падал на кириллице при перенаправлении stdout с cp1252. Новый тест
  воспроизвёл UnicodeEncodeError до исправления и прошёл после явного UTF-8.
- PyTorch relative-path тест использовал checkout и temp на разных Windows drives.
  Изолированный repository root сохраняет проверку разрешения относительных путей
  и устраняет зависимость от расположения дисков.
- Решённый starter в тестовом checkout проходит обычный pytest; тот же код
  отклоняется явным maintainer gate. Проверка артефактов репозитория не отключена.
- Проверка маршрута сохраняет ненулевой pytest exit code, не изменяет progress
  и после технического PASS всё равно требует human review.

## Что нельзя приписывать этой проверке

Самостоятельные внешние проекты ученика не выполнены. Offline tests не подтверждают
качество pretrained модели или генератора. Контейнер, PostgreSQL и cloud должны
иметь отдельное свидетельство запуска: наличие инструкции/Dockerfile не равно
проверенному deployment. Для результатов отдельных runtime-команд выше явно
указывается, какие из них выполнены в этой среде.

В этой среде **не запускались** Docker/Podman, внешний PostgreSQL, AWS deployment,
GPU training, новый live MiniLM/Ollama heldout-эксперимент. Pretrained веса не
скачивались для завершения этой доработки. Эти пункты остаются явными дальнейшими
проверками по соответствующим инструкциям, а не скрытыми условиями общего pytest.

Навигация: [текущая карта](learning-map.md), [рубрика](readiness-assessment.md),
[сравнение с вакансиями](job-market-comparison-2026-10-29.md).

## Оставшиеся границы assessment после финальной доработки

Добавлены learner cases для PCA с тремя признаками/k=2 и уникального промежуточного
шага boosting. Общий artifact gate требует центральную пару `linear` → `tree`
или `tfidf_linear` → `adapted_encoder` соответственно проекту. Live RAG меняет
learner `answer_case`, сохраняя author encoder/pooling; learner `pool_tokens`
оценивается отдельно offline. Реализация external runner и независимый rerun
остаются частью человеческой защиты; допустим альтернативный собственный entry point.

M5 отложен: редкое повторное использование OS PID может ложно отклонить честный
lifecycle restart. Часть semantics request/attachments также остаётся ручной:
saved JSON не требует категории входа и численного deadline второго probe;
человек сверяет их с кодом/логами, обычные child logs, environment details и
статусы Docker/cloud. Новые поля runtime schema не добавлены. `NOT_RUN` для
невыполненного deployment и успешный исход deadline probe остаются допустимыми.

Точное focused evidence этой волны: `.venv/bin/python -m pytest` с тремя node IDs
`modules/04_machine_learning/exercises/linear_geometry/test_starter.py::test_pca_retains_two_ordered_components_in_three_features`,
`modules/04_machine_learning/exercises/tree_boosting/test_starter.py::test_validation_selects_unique_intermediate_snapshot_for_query_predictions`,
`projects/external_tabular/test_evidence.py::test_central_bootstrap_pair_is_required_for_each_project`
и `-q -rx` дал **2 passed, 2 xfailed in 1.71s**. Xfail сохраняет незаполненные
starter boundaries. Две metadata-проверки принимают корректные пары и отклоняют
все остальные пять направленных пар каждого проекта после пересчёта arithmetic/hashes;
вместо model fit используются фиксированные predictions текущего author fixture.
Дополнительная in-memory проверка новых assertions приняла два независимых
reference cases и отклонила семь mutants (PCA: одна компонента, переставленные
eigenpairs, повтор basis, неверная плоскость; boosting: final/baseline predictions,
выбор последнего шага). Starter-файлы и author algorithms не изменялись.
Scoped Ruff check/format прошли для четырёх изменённых Python-файлов;
`git diff --check` прошёл, Markdown diff и локальные ссылки просмотрены.
Повторных дорогих проверок не было: полный pytest/mypy, external training/model
replay, загрузки, TCP/benchmarks, Docker и cloud в этой волне не запускались.
