# R02–R12: материалы, проверки и незавершённые runtime-этапы

Дата: 11.10.2026. Репозиторий `C:/ProjectsDirectory/AIML/_road`, ветка
`codex/ai-ml-wave1`, HEAD `836028944eceaa260cb47d0056b593af4a4648d4`.
Работа продолжена поверх существующих локальных изменений, не поверх старой main.
R01 уже был подготовлен: [его отдельный отчёт](r01-verification.md).
Этот журнал фиксирует первый локальный этап. Последующие установки и фактические
MLflow/Qdrant/PEFT проверки записываются отдельно:
[продолжение runtime-экспериментов](local-runtime-continuation.md).

## Что подготовлено

| Пакет | Открыть | Что действительно есть |
| --- | --- | --- |
| R02 | [Backend: проверки и ссылки](r02-verification.md) | Переходы validators/session/fixture/index; разобранные примеры и 16 авторских тестов |
| R03 | [A1](../projects/document_intelligence_lab/part_a1/README.md), [CI](continuous-integration.md) | Dataset/split identity, rules и fitted TF-IDF baseline, повторная загрузка, отдельный student contract; CI настроен, hosted запуск NOT_RUN |
| R04 | [API](../projects/document_intelligence_lab/service/README.md), [tracking](../projects/document_intelligence_lab/tracking_intro/README.md) | Настоящий локальный ASGI lifecycle/recovery; рецепт контейнера и MLflow adapter, их runtime NOT_RUN |
| R05 | [Cloud: решения до запуска](../projects/document_intelligence_lab/deployment/README.md) | Объяснение и незаполненная launch card; provider/region/budget AWAITING_CHOICE |
| R06 | [Rules → TF-IDF → encoder](../projects/document_intelligence_lab/part_a/README.md) | Единые test IDs, сохранение/загрузка локального случайного encoder; pretrained study NOT_RUN |
| R07 | [RAG](../labs/03_real_rag/README.md) | Corpus/permissions/citations, retrieval и answer отдельно, failure/no-answer, локальные dense mechanics; Qdrant/pretrained/LLM NOT_RUN |
| R08 | [Обязательный vLLM](../labs/05_model_serving/README.md) | Linux preflight, streaming client, ограниченный smoke, измерительные контракты, теория памяти; настоящий Linux/GPU/vLLM NOT_RUN |
| R09 | [Lifecycle](../labs/06_ml_lifecycle/README.md) | Связанные release bytes, monitoring windows, восстановление классификатора; полный registry/index runtime NOT_RUN |
| R10 | [Интеграция](../projects/document_intelligence_lab/architecture.md) | Локальная композиция классификации и bounded retrieval; пустой шаблон самостоятельной защиты |
| R11 | [LoRA и SFT](../labs/04_llm_finetuning/README.md) | Проверенные механика low-rank update и loss mask; это не готовая реализация PEFT/SFT, она BLOCKED_RUNTIME; QLoRA NOT_RUN |
| R12 | [Пути специализации](superpowers/plans/2026-10-11-remaining-roadmap.md#r12) | Только варианты и prerequisites, без новых курсов, зависимостей и заданий |

Общая [карта покрытия](wave2-coverage.md#remaining-integration) разделяет объяснение,
пример, визуальную опору, самостоятельную вариацию и проверку. Существующие уроки
использованы как prerequisites. Демонстрации не подменяют самостоятельную работу.

## Архитектура и сохранность

- Один общий контракт dataset/split/artifact для A1, API, сравнения encoder и
  lifecycle. SHA-256 проверяет соответствие bytes, но не доверенность источника.
  Pickle разрешён только для явно доверенного локального авторского artifact.
- Добавлен только один exercise ID: `document-a1-reproduction`, со своими двумя
  test targets. Прежние 162 ID/порядок/targets сохранены; всего 163 материала.
- `test` допускает ожидаемые учебные xfail; `check <ID>` требует завершить только
  выбранное задание. CLI и progress не переписывались.
- Основные зависимости/lock не изменены. CPU training остаётся отдельным
  окружением; torch не попал в лёгкий базовый install. vLLM не установлен в Windows.
- Новые эксперименты пишут в новые локальные ignored-каталоги `artifacts/`,
  не перезаписывая предыдущие runs и ученические отчёты.

[Полный перечень новых и изменённых файлов](remaining-roadmap-files.md).
SHA-256 сверка с начальным снимком: из 920 прежних файлов **902 побайтно сохранены**,
18 перечисленных навигационных/регистрационных файлов дополнены; **109 новых**,
удалений нет. Старые learner implementations, отчёты, progress, CLI и `uv.lock`
не изменены. Ветка и HEAD совпадают с исходными.
Независимые проверки отдельных пакетов и интеграции проведены; замечания об
identity токенизатора, строгости JSON scalar types и обработке streaming errors
закрыты regression-тестами. Использование test-first и независимого review
повлияло на эти границы, а не на ответы в ученических TODO.

## Технические проверки

Все команды ниже запускались из корня репозитория, в уже существующих окружениях.
Python 3.12.14; базовые numpy 2.5.3, pandas 3.0.6, sklearn 1.9.1;
training: torch 2.14.0+cpu, transformers 5.17.0, datasets 5.0.1. CUDA в этом
training-окружении нет. Реальный GPU host: RTX 5060 Laptop, 8151 MiB, driver 616.64.

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv-training/Scripts/python.exe -m pytest labs projects/document_intelligence_lab -q
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy
.venv-training/Scripts/python.exe -m mypy -p labs -p projects.document_intelligence_lab
```

Последние завершённые прогоны: base **1294 passed, 55 skipped, 1162 xfailed**;
training **352 passed, 1 skipped, 70 xfailed**. Оба exit 0. Skips/xfails не зачтены
как реализованные learner TODO или optional runtime. В каждом один upstream
`Starlette/AnyIO BlockingPortal` deprecation warning — не скрыт обновлением зависимостей.
Ruff — passed; форматирование — **972 файла**; base mypy — **683 source files**.
Training mypy — **111 source files**, no issues.

В первом интеграционном прогоне были найдены пропущенная запись нового ID в
проверке repository hygiene и ссылки на ещё создававшиеся runbooks. Запись добавлена,
документы завершены; итоговые прогоны не содержат этих ошибок. Ранний training mypy
также выявил нетипизированный test helper vLLM client — исправлен без смены API.
Один дополнительный regression был запущен раньше создания этого отчёта и поймал
две ссылки на ещё отсутствовавший файл. После завершения документации полный
прогон повторён; это не было проигнорировано как допустимая ошибка.

Проверка установки здесь **не равна новой установке**:

```powershell
uv sync --locked --offline --dry-run
$env:UV_PROJECT_ENVIRONMENT = '.venv-training'
uv sync --locked --offline --dry-run --group training
Remove-Item Env:UV_PROJECT_ENVIRONMENT
```

Оба dry-run exit 0, lock разрешает 199 packages. Первый предложил переустановить
локальный проект; второй также предложил удалить семь установленных visualization
packages, так как эта группа не указана. Ничего не применялось. При последующей
реальной синхронизации существующего plotting-окружения сохраняйте нужную группу
`--group visualization`. Свежий base/training install этой итерацией **не проверен**.
MLflow/Qdrant/PEFT/accelerate/bitsandbytes/vLLM не устанавливались.

## Не только pytest: что реально запускалось

- A1: обучение TF-IDF только на train, сохранение всех evidence, reload и
  повторный inference. Teacher имеет известные ошибки; протокол не скрывает их.
- API: настоящие TestClient lifespans A → B → отказ на неверном hash → A;
  ответ для `triangle` меняется circle → triangle → circle. Это ASGI, не TCP,
  контейнер, облако или production benchmark.
- R06: `.venv-training/Scripts/python.exe -m projects.document_intelligence_lab.part_a.demo --output artifacts/document-a-teacher-author-001`.
  Input/mask `[2,5]`, logits `[2,3]`, reload parity true. На шести общих test IDs:
  rules accuracy 2/3, macro-F1 5/9; TF-IDF 1 и 1; случайный encoder 1/3 и 1/6.
  Это маленькая синтетическая задача, не оценка pretrained модели или обобщения.
- R07: локальные retrieval/answer runs и random-model dense mechanics;
  `local_files_only` не разрешает скрытый download. Pretrained inventory обязан
  совпасть с закреплённым набором regular files: дополнительные tokenizer файлы,
  ссылки и вложенные каталоги отвергаются до загрузки.
- R09: фактические release bytes и новый classifier lifespan, отдельно fresh-process
  restoration; [измеренные результаты и ограничения](../labs/06_ml_lifecycle/verification.md).
- R10: `.venv/Scripts/python.exe -m projects.document_intelligence_lab.integration_demo --output artifacts/document-integration-author-001`.
  Проверены known/outage/deleted/private/absent, без внешней LLM и автономного loop.
  Общая «AI accuracy» не выдумана: разные задачи имеют разные оценки.
- R11: pure PyTorch rank-1 update, loss 4.5 → 0.0449999869; 5 trainable и
  6 frozen parameters; правильный base checkpoint восстанавливает ответ,
  неправильный — нет. Это механический пример, не PEFT-compatible adapter.

## Документация и визуальная проверка

Проверены **318 Markdown-файлов, 0 broken local targets**, включая untracked;
**52 anchors** в выбранных 46 документах, 0 ошибок. Дополнительно запущены
`tests/integration/test_markdown_links.py` и `tests/tooling/test_documentation.py`
в составе полного regression. `git diff --check` — exit 0.
Временный локальный preview использовал уже установленный Mistune: просмотрены
основные страницы R02/R06/R07/R08/R09/R10/R11/R12, таблицы и кодовые схемы;
реальные SVG recovery/monitoring открыты в браузере. Для схем без отдельного
renderer использован читаемый ASCII. Временный preview не является частью курса.
Это не проверка всех страниц в GitHub/PyCharm и не клики по каждому navigation link.

## Что остаётся сделать явно

1. Выбрать окружения и отдельно разрешить/выполнить installs для MLflow, Qdrant,
   PEFT. После этого проверить реальные integrations; отсутствие пакетов не
   заменено mock-заявлением об успехе. Полная PEFT/SFT реализация ещё не подготовлена.
2. Для обязательного vLLM выбрать Linux runtime (WSL2 или отдельный Linux GPU host),
   проверить CUDA/версию/ресурсы и только затем явно загрузить выбранную модель.
   Кандидаты и ограничения RTX 5060 — в [compute guide](compute-guide.md).
3. Для cloud сначала заполнить provider/region/budget/access/cleanup решения.
   Docker, WSL, cloud, hosted CI и настоящий endpoint этой итерацией не запускались.
4. Выполнить собственные model/data эксперименты и защитить решения. Learner
   progress не повышен; новые отчёты оставлены пустыми. Зелёный pytest не доказывает
   качество модели, честный эксперимент или понимание темы.

## С чего начинать ученику

Если начинаете с нуля — [основной roadmap](roadmap.md) и существующий Python Core.
R02–R12 не заменяют prerequisites. После готовых Data/ML и backend:

```powershell
.venv/Scripts/python.exe scripts/learn.py list
.venv/Scripts/python.exe scripts/learn.py test document-a1-reproduction
.venv/Scripts/python.exe scripts/learn.py check document-a1-reproduction
```

Сначала [A1 README](../projects/document_intelligence_lab/part_a1/README.md), затем
theory → teacher demo → самостоятельное exercise. Нетронутое задание закономерно
не получает `check`: ожидаются 12 passed, 2 xfailed и exit 1 (CHECK INCOMPLETE).
`test` тех же материалов допускает эти xfail и возвращает 0. Не удаляйте xfail
или тесты ради зелёного зачёта — реализуйте TODO и собственный evidence.

Commit/push/merge, model/data downloads и изменения старого student progress
не выполнялись. «Локальные материалы подготовлены» не означает «все PLANNED
runtime-этапы завершены».
