# Теоретический пакет 6 — LLM Engineering и RAG

Пакет углубляет существующие Module 05 и Module 06. Он не является новой
real RAG лабораторной и не подтверждает прохождение материала учеником.
Репозиторий: `C:\ProjectsDirectory\AIML\_road`, ветка `codex/ai-ml-wave1`,
HEAD `836028944eceaa260cb47d0056b593af4a4648d4`. Дата: 04.10.2026.

Материалы подготовлены; локальная механика проверена. Это не результат
оценки настоящей модели и не зачёт самостоятельной работы ученика.

## Как проходить

Сначала откройте [Module 05 README](../modules/05_llm_engineering/README.md).
Сохраняются его prerequisites: Modules 01–03; Module 04 помогает с оценкой.
Материал HF/attention пакета 5 используется как поясняющая ссылка, а не как
новая обязательная установка `training` для этого модуля.

1. Читайте уроки LLM 01–06 в прежнем порядке. До запуска прогнозируйте решение
   приложения и объясняйте, какой проверки ещё не хватает.
2. Запустите преподавательский LLM-сценарий; сопоставьте вопрос, источник,
   заранее заданный ответ и этап его принятия или отклонения.
3. Самостоятельно решайте прежние prompt/structured-output/budget/evaluation/
   reliability задания. Демонстрация не является вашим submission.
4. После Module 05 переходите к [Module 06 README](../modules/06_rag/README.md)
   и его урокам 01–06: происхождение данных → разбиение → поиск →
   объединение/переранжирование → контекст → оценка.
5. Предскажите найденные фрагменты и запустите retrieval-сценарий. Объясните
   различие промаха поиска и отсутствия информации в корпусе.
6. Выполните старые самостоятельные задания и защитите ограничения выводов.

Из PowerShell, после обычной установки существующего базового окружения:

```powershell
Set-Location C:\ProjectsDirectory\AIML\_road
.venv/Scripts/python.exe -m modules.05_llm_engineering.walkthrough --output generated-reports/my-llm-contract-01
.venv/Scripts/python.exe -m modules.06_rag.walkthrough --output generated-reports/my-retrieval-01
```

Для повторного запуска выберите **новое** имя каталога. Существующие результаты
не перезаписываются. Эти команды не скачивают модель или датасет.

После собственной реализации используйте прежний CLI, например:

```powershell
.venv/Scripts/python.exe scripts/learn.py test llm-event-contract
.venv/Scripts/python.exe scripts/learn.py check llm-event-contract
.venv/Scripts/python.exe scripts/learn.py test rag-retrieval-evaluation
.venv/Scripts/python.exe scripts/learn.py check rag-retrieval-evaluation
```

`test` допускает xfail незавершённых работ; `check ID` — строгая проверка
конкретной ученической реализации. Создание теории и зелёные author tests
не меняют progress и не расширяют старый зачёт.

## Что создано и зачем

В существующих шести уроках каждого модуля появляются соседние `theory.md`;
README остаются входом и получают короткие ссылки. Старые examples сохраняют
прежние проверяемые API. Отдельные walkthrough нужны для связных трасс, которые
не расширяют контракты прежних демонстраций и самостоятельных задач.

Часть А использует вымышленный справочник велосервиса `G-01` и заранее
подготовленные completion. В отличие от ученического event-контракта, здесь
нет готового решения дат/часовых поясов/площадок; в отличие от budget/retry/
stream/cache задач — нет реализации их полных алгоритмов. Параметры генерации
объясняются численно, но реальная генеративная модель не запускается.

Часть Б продолжает тот же предметный пример: реальные локальные вычисления
TF-IDF, ранжирование, происхождение контекста и иллюстративный ответ. Это не
pretrained embeddings, обученный reranker или развёрнутый vector database.
Ученические ranking fixtures и итоговые отчёты не используются как готовый
преподавательский ответ.

Формат наглядности — небольшие таблицы и текстовые трассы. Они доступны без
notebook; Matplotlib, новая визуальная библиотека и отдельный frontend не нужны.
Авторские тесты находятся в `tests/integration/test_packet6_*.py`, вне прежних
curriculum test targets. Новых exercise ID нет.

### Файлы этого пакета

Новые файлы (17):

- [LLM 01 theory](../modules/05_llm_engineering/01_llm_interfaces/theory.md),
  [02](../modules/05_llm_engineering/02_prompt_contracts/theory.md),
  [03](../modules/05_llm_engineering/03_structured_outputs/theory.md),
  [04](../modules/05_llm_engineering/04_context_and_cost/theory.md),
  [05](../modules/05_llm_engineering/05_evaluation/theory.md),
  [06](../modules/05_llm_engineering/06_reliability_and_tools/theory.md).
- [RAG 01 theory](../modules/06_rag/01_retrieval_contracts/theory.md),
  [02](../modules/06_rag/02_ingestion_chunking/theory.md),
  [03](../modules/06_rag/03_lexical_dense_retrieval/theory.md),
  [04](../modules/06_rag/04_hybrid_reranking/theory.md),
  [05](../modules/06_rag/05_grounded_answers/theory.md),
  [06](../modules/06_rag/06_rag_evaluation/theory.md).
- [LLM walkthrough](../modules/05_llm_engineering/walkthrough.py),
  [RAG walkthrough](../modules/06_rag/walkthrough.py).
- [LLM author tests](../tests/integration/test_packet6_llm.py),
  [RAG author tests](../tests/integration/test_packet6_rag.py).
- Этот единый итоговый отчёт.

Из существующих файлов изменены только 14 README (два модуля и их 12 уроков)
с входными ссылками и [карта покрытия](wave2-coverage.md#theory-packet-6)
с добавленным разделом. Старый текст карты не заменён. Игнорируемые teacher
traces и временный HTML-предпросмотр не являются learner submissions.

## Реальные проверки

Базовое окружение: Python 3.12.14, NumPy 2.5.3, pandas 3.0.6,
scikit-learn 1.9.1, Pydantic 2.13.5, pytest 9.1.1, Ruff 0.16.8, mypy 2.3.1.
В нём отсутствуют `torch`, `transformers`, `matplotlib` (проверено `find_spec`).

Исходная регрессия до изменений пакета:
`.venv/Scripts/python.exe -m pytest -q` → **970 passed, 50 skipped,
1160 xfailed**, 108.80 s. Одно существующее предупреждение Starlette
об устаревающем имени AnyIO `BlockingPortal`; оно не подавлялось.

Проверки части А до начала Б:

| Команда | Наблюдаемый результат |
| --- | --- |
| `uv sync --locked --offline --dry-run` | Exit 0; 156 packages checked, would make no changes; это проверка соответствия, не новая установка |
| `.venv/Scripts/python.exe -m pytest tests/integration/test_packet6_llm.py modules/05_llm_engineering -q` | 56 passed, 112 xfailed; повтор контроллера 2.54 s |
| `.venv/Scripts/python.exe -m mypy -p modules.05_llm_engineering` | Success, 46 source files |
| `.venv/Scripts/python.exe -m ruff check .` | All checks passed на состоянии после А |
| `.venv/Scripts/python.exe -m ruff format --check .` | 834 files already formatted на состоянии после А |
| `.venv/Scripts/python.exe -m mypy` | Success, 628 source files на состоянии после А |

Независимое ревью А: нет критических/существенных замечаний. Его небольшое
уточнение внесено: `permission` поступает из доверенной логики приложения,
а teacher-функция не реализует аутентификацию.

Проверки конечного кода пакета:

| Команда | Наблюдаемый результат |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/integration/test_packet6_rag.py modules/06_rag -q` | 77 passed, 89 xfailed, 4.92 s |
| `.venv/Scripts/python.exe -m pytest tests/integration/test_packet6_llm.py tests/integration/test_packet6_rag.py modules/05_llm_engineering modules/06_rag -q` | 133 passed, 201 xfailed, 7.69 s; новые author cases — 28 passed |
| `.venv/Scripts/python.exe -m pytest -q` | 998 passed, 50 skipped, 1160 xfailed, 1 прежний warning, 107.79 s |
| `.venv-training/Scripts/python.exe -m pytest -q` | 1105 passed, 6 skipped, 1224 xfailed, 1 прежний warning, 164.58 s |
| `.venv/Scripts/python.exe -m ruff check .` | All checks passed |
| `.venv/Scripts/python.exe -m ruff format --check .` | 842 files already formatted |
| `.venv/Scripts/python.exe -m mypy` | Success, 629 source files |

Полная проверка существующего `.venv-training` включает установленные
training и visualization. В нём уже установлены torch 2.14.0+cpu,
Transformers 5.17.0 и Matplotlib 3.11.2. Они не стали зависимостями новых уроков.
Новая чистая установка — **NOT_RUN**: зависимости не менялись, проверено
соответствие текущего base окружения lock-файлу через offline dry-run.
Отдельное GPU-окружение — **NOT_RUN** и для этого пакета не требуется.
xfail/skip не выдаются за выполненные ученические задания; CLI `check` за ученика
не запускался. В финальном base прогоне на 28 успешных author cases больше
исходного, число прежних xfail/skip совпадает с исходной регрессией.

Итоговое независимое ревью всего пакета: **spec PASS, quality PASS**,
критических/существенных замечаний и оставшихся обязательных исправлений нет.
Ревью отдельно воспроизвело offline-механику и сверку сохранности; полные suite
не дублировало. Результаты двух полных прогонов выше получены контроллером.

### Числа и отображение части А

Реально запущена команда LLM walkthrough с новым каталогом
`generated-reports/teacher-packet6-a-verified-02`. В `trace.json` бюджет:
`15+20+10+35+0=80`, резерв `20`, общий учебный лимит `100`.
Это условные единицы, не результат tokenizer. Семь решений:
`accepted`, `evidence_failure`, `access_denied`, `refused`, `truncated`,
`schema_failure`, `empty` — соответствуют семи именованным случаям.
Защищённый запрос посетителя не содержит context/completion.

Отдельно арифметика через стандартные `Fraction`/`Decimal` подтвердила:
при условном распределении `0.6/0.3/0.1` и `top_p=0.8` оставленная масса
`9/10`, нормированные вероятности `2/3` и `1/3`; старый пример цены даёт
`0.0048` при заданных учебных usage и ставках. Это не sampling настоящей модели.

Шесть теорий А: 28 локальных ссылок, один якорь, четыре таблицы и один code fence
проверены отдельным author QA. Установленный Mistune преобразовал текст в HTML
для локального просмотра: во всех шести страницах распознаны заголовки/таблицы,
горизонтального переполнения страницы не обнаружено. Таблица проверок ответа
также визуально просмотрена в браузере. Это проверка временного локального
предпросмотра, не обещание одинакового отображения во всех Markdown-редакторах.

### Числа, поведение и отображение части Б

Контроллер выполнил:

```powershell
.venv/Scripts/python.exe -m modules.06_rag.walkthrough --output generated-reports/teacher-packet6-b-verified-01
```

Его `trace.json` побайтно совпал с финальной трассой разработчика
`teacher-packet6-b-02`: SHA-256
`945DD3A9CBC27EBCF851094091317D1C176E6F3294DA11CE122804BCA1C41FD7`.

| Случай | Вычисленный retrieval | Финальное решение |
| --- | --- | --- |
| found | G-01@2026-09:p1, 0.525060 | Иллюстративный ответ с этим chunk |
| missed | Нет положительного score для `night shelter` | Воздержание при известном автору релевантном G-01 |
| absent | Нет положительного score для `battery warranty` | Воздержание; авторская разметка не содержит ответа |
| stale | G-01@2026-08:p1, 0.572225 | Chunk отклонён проверкой текущей ревизии |
| conflict | G-01 0.461268; G-07 0.335107 | Оба текущих passage сохранены, ответ отклонён по авторской политике конфликта |
| protected | Нет пользовательских кандидатов | Закрытый источник исключён до поиска |

Scores получены TF-IDF/cosine, а не подобраны вручную. Разные snapshots дают
разные IDF; числа между случаями не являются шкалой достоверности.
Повторный запуск конечного кода в `teacher-packet6-b-final-01` дал тот же SHA-256.
Независимая арифметика подтвердила RRF `1/61+1/62=0.03252247488101533`,
smooth-IDF cosine тестового примера `0.9321916852554909` и macro Recall@1
двух фактических выдач `(1+0)/2=0.5`. Обобщённые metric/RRF TODO не реализованы.

Проверены нулевой словарь, пустой результат, стабильные ties, смена прав,
ревизии, подмена chunk и ограничение бюджета; citations принадлежат финальному
context. Повторная запись запрещена даже в уже существующий пустой каталог.
Кроме author tests, отдельный Python-процесс с заблокированными
`socket.socket.connect`/`socket.create_connection` импортировал оба walkthrough,
вычислил RAG cases и сохранил новую трассу `teacher-packet6-b-offline-01`.
Это проверка данного локального пути выполнения, не общая гарантия безопасности.

По независимому ревью Б уточнена причина отказа при уменьшенном бюджете:
`conflict` с budget 0 или 60 даёт `abstain_context_budget`, с 1000 —
`abstain_conflict`. Усилен тест конкурирующего закрытого/открытого hit при
top-k=1 и пояснена смена единицы chunk→document в прежних заданиях.
Повторное ревью подтвердило все три уточнения; новых поломок не обнаружено.

Все 12 новых теорий просмотрены в локальном HTML-предпросмотре: заголовки и
таблицы присутствуют, горизонтального переполнения страницы не обнаружено.
Визуально просмотрены таблицы pipeline, structured-output checks и оценки.
Текстовые схемы chunking, ranking и context сопоставлены с реальной трассой.
Графики и notebook не создавались: здесь таблицы и трассы точнее показывают механизм.

Локальная проверка 28 документов (14 README, 12 теорий, дополнение карты и отчёт):
159 ссылок, два якоря, 17 таблиц и 22 fenced-блока проверены. Проверялись
существование целей/якорей, закрытие fences и одинаковое число столбцов;
Python-fences в новых теориях отсутствуют, вместо них запускаются walkthrough.
Исходящие ссылки временного HTML не переписывались; пути проверены по Markdown,
а не кликами по неподдерживаемому HTML-маршруту. Карта покрытия также просмотрена.
`.venv/Scripts/python.exe -m pytest tests/integration/test_markdown_links.py -q`
даёт **3 passed**; отдельный author QA дополнительно охватывает новые untracked файлы.

Первичные внешние ссылки открыты и сверены: Python 3.12, scikit-learn 1.9,
Hugging Face 5.17, Pydantic strict/JSON, Stanford IR Book, исходные RRF/RAG
статьи, AWS retry guidance и Anthropic evaluation guidance. В уроках указаны
конкретные разделы и цель чтения; это не требует устанавливать их платформы.

### Сохранность

Сверка SHA-256 с начальным снимком 868 файлов показала изменения только
15 существующих файлов, перечисленных выше; остальные 853 совпадают.
В частности, `progress.md`, curriculum/CLI, старые examples/tests, student TODO,
`pyproject.toml`, `uv.lock` и предыдущие пакеты не переписаны.
Хеш `progress.md`:
`9C78D95D05EFB7234C8B3412D072577916A11192531AEE1B27A0DF60CE647DC0`.
HEAD и ветка не изменились. Установки зависимостей, загрузок моделей/датасетов
и внешних действий нет; чтение публичной документации не запускало ML-эксперименты.

## Границы результата

Техническая проверка локальных механизмов не измеряет качество настоящей LLM.
Pretrained embeddings, внешний provider, постоянный векторный индекс, реальные
latency/cost и модельное качество — **NOT_RUN**. Будущая
[real RAG lab](../labs/03_real_rag/README.md) остаётся **PLANNED**.
Понимание, самостоятельные TODO и содержательная защита — **REQUIRES_REVIEW**.
Следующее теоретическое углубление Agents/workflows и Production AI — **PLANNED**.
Commit/push/merge не выполнялись.
