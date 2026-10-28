# Остаток Ml_roadmap: теория, самостоятельная практика и реальные системы — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** закрыть фактические пробелы существующей программы, реализовать согласованные
следующие этапы небольшими проверяемыми пакетами, не создавать второй курс.

**Architecture:** существующие уроки — prerequisites; Document Intelligence — один
сквозной проект; labs 03–06 — специализированные продолжения. Сначала CPU/offline,
затем явные модельные/сервисные эксперименты. Вводный A1/API не подменяет полные labs.

**Tech Stack:** действующие Python/uv, pytest/Ruff/mypy, NumPy/pandas/scikit-learn,
FastAPI/SQLAlchemy; opt-in PyTorch/HF и Matplotlib. Будущие Qdrant, MLflow, PEFT,
vLLM — только в нужном пакете и отдельном окружении/группе, не в лёгком старте.

**Spec:** [согласованные пять этапов и 20 коротких блоков](../../ai-ml-extension-plan.md),
[последний аудит](../../wave2-coverage.md#route-integration-audit),
[ресурсный профиль](../../compute-guide.md#rtx5060-profile),
[Document Intelligence](../../../projects/document_intelligence_lab/README.md).

Дата сверки: **11 октября 2026**. Ветка `codex/ai-ml-wave1`, исходный HEAD
`836028944eceaa260cb47d0056b593af4a4648d4`; локальные изменения сохранены.
Это **план с поэтапным исполнением**: R01/R02 подготовлены; локальные авторские
материалы R03–R11 реализованы в границах таблицы ниже, внешние runtime-этапы
не завершены. [Проверки и ограничения](../../remaining-roadmap-verification.md).
R12 по уточнению пользователя — только навигатор.
[Текущее продолжение runtime-проверок](../../local-runtime-continuation.md):
отдельные opt-in окружения MLflow/Qdrant/PEFT, без model/data downloads.
[R01: результаты проверок и границы](../../r01-verification.md). Все флажки ниже — работа автора,
не student progress. Номера R01–R12 — организационные метки, **не exercise ID**.

## Global Constraints

- Не переписывать готовые Object Model, Collections, Functions, Typing, NumPy,
  Pandas/EDA, статистику, классическое ML, training bridge, attention и модули 05–08.
  Ссылка на prerequisite предпочтительнее повторного объяснения целого урока.
- Не трогать learner implementations, TODO, отчёты и progress. Новая нейтральная
  демонстрация не должна быть решением старого задания под другим названием.
- Сохранять CLI, ID и контракты. `test` допускает существующие учебные xfail;
  `check <ID>` строго проверяет только выбранное выполненное задание. Не запускать
  глобальный зачёт, который красный из-за будущих TODO. Новый ID — только для
  действительно нового оцениваемого умения, с собственным scoped check.
- Не добавлять курсы Git/Linux/технического английского. Теория и новые защиты —
  на русском с английскими терминами; старые контракты не переименовывать.
  Для vLLM нужна короткая инструкция Linux runtime, а не отдельный курс ОС.
- Не устанавливать WSL, контейнеры/сервисы, не скачивать модели/датасеты, не создавать
  облачные ресурсы и не отправлять данные внешним API без явного действия пользователя.
  Обычные import/pytest/uv sync не загружают модельные artifacts.
- Не выполнять commit/push/merge и не заменять рабочую копию старой main.
  Реальный hosted CI потребует отдельного разрешения на публикацию/запуск.
- vLLM **обязателен**, даже если понадобится другой Linux host. Его оптимизация,
  LoRA и прочие специализации не становятся обязательными вместе с базовым vLLM.

## Фактическое покрытие, а не поиск слова PLANNED

| Что есть сейчас | Источник | Что с этим делать |
| --- | --- | --- |
| Теоретические пакеты 1–7 READY | [карта покрытия](../../wave2-coverage.md#route-integration-audit) | Переиспользовать; ранние PLANNED внутри исторических отчётов уже перекрыты поздними пакетами |
| 14 продолжений Wave 2 READY: статистика, tabular, resume/diagnostics/attention, data release, product/evaluation, ranking/forecasting intro, interview/SQL | [Wave 2 prerequisites и ID](../../wave2-coverage.md) | Не создавать их заново; исследования ученика и ручная защита остаются отдельными |
| Шесть исходных NEEDS_DEPTH в Python/backend | [исходный аудит](../../wave2-coverage.md#route-integration-audit), [R01](../../wave2-coverage.md#remaining-r01), [R02](../../wave2-coverage.md#remaining-r02) | Python и backend переходы дополнены; самостоятельное освоение отдельно |
| Новые самостоятельные вариации, SQL plan/index, A1/CI/API/tracking/cloud | [этапы 1–3](../../ai-ml-extension-plan.md#five-stage-plan) | R01/R02 и A1/API подготовлены; tracking/cloud runtime отдельно; [CI](../../continuous-integration.md) CONFIGURED, hosted run NOT_RUN |
| Labs 03–06 и Document Intelligence — локальные механизмы, теория и runtime-рецепты | [RAG](../../../labs/03_real_rag/README.md), [SFT](../../../labs/04_llm_finetuning/README.md), [serving](../../../labs/05_model_serving/README.md), [lifecycle](../../../labs/06_ml_lifecycle/README.md), [проект](../../../projects/document_intelligence_lab/README.md) | Offline scope и отдельные actual local PEFT/Qdrant/MLflow опыты проверены; не приравнивать к pretrained, сквозной интеграции или vLLM запуску |
| GPU, pretrained studies, PostgreSQL/cloud и learner reports не подтверждены | [границы предыдущих проверок](../../wave2-verification.md), [вычислительная среда](../../compute-guide.md) | Отдельные явные experiments/review; NOT_RUN не равно отсутствующей теории |
| Глубокие специализации | [развитие маршрута](../../ai-ml-extension-plan.md) | R11/R12 по выбору, не общий список обязательных технологий |

## Порядок и размер пакетов

Это порядок **подготовки оставшихся материалов**. Новичок начинает с существующего
Python Core, а не с R01/vLLM; готовые prerequisites не пропускаются.
Каждый пакет выдавать небольшими частями: один механизм → demo → вариация → проверка.
Не превращать 20 ранее намеченных блоков в 20 новых обязательных ID.

| Пакет | Что остаётся подготовить | Когда в обучении | Статус |
| --- | --- | --- | --- |
| R01 | Три пробела Python + debugging/test design/decomposition | После соответствующих уроков Python; перед A1 | CORE / READY; ученик REQUIRES_REVIEW |
| R02 | Три пробела backend + SQL plan/index | После Python и соответствующих backend уроков | CORE / READY; [проверки](../../r02-verification.md) |
| R03 | Dataset → rules/classical A1 → воспроизводимость → CI | После готовых Data/ML и R01; SQL после R02 | A1 материалы READY; CI CONFIGURED, hosted NOT_RUN |
| R04 | CPU API → контейнер → вводный tracking → rollback | После R03 и backend/R02 | ASGI/rollback и local MLflow runs/flavors/replay проверены; container NOT_RUN |
| R05 | Одно настоящее cloud deployment | После R04; provider/budget gate, не блокирует локальный R06 | Теория готова; AWAITING_CHOICE, deployment NOT_RUN |
| R06 | Полная часть A: существующие PyTorch/HF → encoder comparison | После обеих labs и R03; теория уже READY | Local random-model integration и inventory/cohort preflight подготовлены; pretrained NOT_RUN |
| R07 | Real RAG + основа части B | После R06, LLM/RAG и experiment protocol | Actual local Qdrant mechanics PASS; MiniLM CLS retrieval измерен на пяти teacher queries; generator/LLM NOT_RUN |
| R08 | Обязательный Linux vLLM | После R07, backend/HF и локального Production AI | Теория/client/offline checks READY; DEFERRED_ENV по решению пользователя 11.10.2026, runtime NOT_RUN |
| R09 | Полный lifecycle: данные, registry, monitoring, recovery | Полный этап после обеих labs, R08 и модуля 08; local registry/recovery доступны раньше | Actual coupled local classifier+MiniLM corpus/index A→B→A и отдельный MLflow registry проверены; production promotion/drift NOT_RUN |
| R10 | Свести Document Intelligence и защитить решения | После R06–R09 и bounded workflows модуля 07 | Teacher composition и защита подготовлены; learner REQUIRES_REVIEW |
| R11 | SFT → LoRA → условный QLoRA | После основного маршрута, при выборе ML-DEPTH | Actual CPU PEFT/SFT train/save/reload на tiny random LM проверен; pretrained/QLoRA NOT_RUN |
| R12 | Пути и варианты специализаций, без реализации веток | После основной практики и её prerequisites | Навигатор READY; ветки OPTIONAL |

Связи artifacts: `R03 A1 → R04 CPU service → R05 cloud`;
`R03 + готовые labs → R06 encoder → R07 RAG → R08 vLLM → R09 lifecycle → R10 проект`.
R04 даёт ранний опыт tracking/rollback, **не** снимает prerequisites полной R09.
R05 не исчезает при отсрочке согласования; до реального deployment его статус NOT_RUN.
R07 может сначала использовать явно выбранный локальный HF runtime; затем R08
подключает vLLM и повторяет оценку. Так vLLM не становится циклическим prerequisite RAG.

Статусы не означают, что все внешние этапы выполнены. MLflow/Qdrant/PEFT установлены
в отдельных разрешённых opt-in окружениях; actual local runs записаны в
[runtime-протоколе](../../local-runtime-continuation.md). Linux/vLLM явно отложены
пользователем: DEFERRED_ENV / NOT_RUN. После отдельного разрешения скачан только
MiniLM (шесть pinned files, ~92 MB), measured CLS retrieval на teacher corpus.
Другие pretrained опыты, cloud и hosted CI остаются NOT_RUN;
датасеты и GPU kernels не скачивались. Неполные
многочастные пункты ниже остаются без флажка, даже если их теория уже подготовлена.
Ученический progress не связан с этими авторскими флажками.

## Обязательный формат теории и визуализации каждого пакета

Использовать [существующий шаблон](../../theory-lesson-template.md), README — вход.

1. Практический вопрос и прогноз результата до запуска; короткие prerequisites.
2. Русская интуиция, затем точные термины и границы аналогии.
3. Полностью разобранная **другая** демонстрация: код, промежуточные значения,
   наблюдаемый вывод и объяснение каждого существенного перехода.
4. Визуальная опора там, где есть связь/порядок/форма/сравнение: таблица, шкала,
   схема, график. Имена, shapes, единицы, значения и стрелки совпадают с кодом.
5. Типичная ошибка, маленький контрпример, самостоятельная вариация без решения.
6. Вопросы «почему?», «что изменится?», «чего это не доказывает?» и критерий переноса.
7. Конкретные официальные источники: раздел, ссылка, что читать, где остановиться.
   Перед реализацией проверить актуальную версию API, не копировать старый пример вслепую.

Markdown/SVG подходят для состояний и архитектуры; Matplotlib из существующей
opt-in группы — для численных графиков. Notebook только при пользе и с чистым kernel.
Не требовать рисунка для каждого метода. Не добавлять web app, виджеты или библиотеки
ради оформления. Синтетическую кривую помечать учебной; benchmark рисовать только
из сохранённых measurements. У визуала должны быть подписи и текстовое объяснение.

## Review Focus

Пять основных рисков проверять в указанных пакетах, не оставлять на общий финал:

1. **Дублирование или раскрытие решения** — R01/R02/R06, сравнение с текущими TODO.
2. **Смешение test/check, smoke/quality и авторского/ученического статуса** — R03/R07/R10.
3. **Leakage, неверная provenance и несогласованные artifacts** — R03/R06/R09/R11.
4. **Невидимые загрузки, секреты, расходы и неподходящий GPU stack** — R05/R07/R08/R11.
5. **Нарисованные результаты и непроверенное восстановление** — R04/R08/R09/R12.

<a id="r01"></a>

## R01 — Понятные Python-механизмы и самостоятельная разработка

**Вход:** готовые Object Model/Functions/Typing и соответствующие уроки.
**Изменяемые места:** `modules/01_python_core/05_data_modeling/README.md`,
`06_exceptions_io/README.md`, `09_testing/README.md` и их teacher examples;
`modules/01_python_core/tests/test_examples.py`, `test_learning_flow.py`.
Новые demonstrations/tests размещать рядом с этими уроками, не в student starter.

- [x] 1. Разобрать нейтральный value object: конструктор → `__post_init__` → инвариант;
  finite `Decimal`, ASCII против Unicode predicates, границы `frozen`.
  Визуал: таблица вход → состояние полей → объект/ошибка.
  Перенос в существующий `python-payment-model`, не готовая реализация платежа.
- [x] 2. Объяснить atomic I/O на другом небольшом artifact: сериализация и replace —
  разные фазы отказа; закрытие writer, cleanup только собственного temp, исходное исключение.
  Визуал: три временные шкалы успех/serialization failure/replace failure.
  Переиспользовать `python-json-export`, не выдавать его exporter целиком.
- [x] 3. Добавить самостоятельный **выбор тестов** к другой маленькой функции:
  ordinary/empty/invalid/boundary case matrix, дефектный кандидат и независимые assertions.
  Объяснить traceback: стек вызовов → первое нарушенное ожидание → минимальный пример.
  Переиспользовать `python-testing`, `python-mock-provider`,
  `python-debug-mutable-defaults`; старый check не расширять скрытыми требованиями.
- [x] 4. Подготовить нейтральную вариацию обработчика документов для A1:
  validation → transformation → result; Functions и `python-review-stateful-report`
  как prerequisites. Ученик меняет одно требование и проверяет предложенный AI-код
  своим тестом. `python-word-index` уже есть — новой копии не нужно.
- [x] 5. Проверить выводы/схемы; failure tests сохраняют старые bytes и исходную ошибку.
  Для test-design описать contract и ручную приёмку без нового ID. Критерий ученика:
  learner-authored tests реально ловят дефект; **он ещё не проверен**. Пустые tests/report
  сохранены, готовность авторских материалов не означает ученический зачёт.

**Подготовлено 11.10.2026:** три `theory.md` и запускаемых `walkthrough.py`, отдельный
traceback-дефект, outline v1/v2 и дефектный кандидат, 34 авторские проверки + девять
встроенных teacher cases. [Полный состав, команды и ограничения](../../r01-verification.md).
Визуальные опоры — таблицы фаз/состояний и схема, не отдельное приложение.

**Выход:** точечная теория, teacher demos и checks, новая самостоятельная вариация.
**Освоение:** объяснить новую ошибку и придумать свой различающий тест; pytest учителя
не доказывает самостоятельность ученика. CPU/offline.

<a id="r02"></a>

## R02 — Валидация, транзакции, fixtures и один SQL-план

**Вход:** R01 и готовые backend уроки. **Места:**
`modules/02_python_backend/02_pydantic/README.md`, `06_sqlalchemy/README.md`,
`08_api_integration_testing/README.md`, `exercises/analytics_sql/README.md`;
teacher demos рядом, проверки в `modules/02_python_backend/tests/`.

- [x] 1. Нейтральный `field_validator`: parsing → field rule → service/422;
  показать фактический error `loc`, не только сказать «валидация».
  Связь с `backend-transaction-contract`; сервис не вызывается для rejected input.
- [x] 2. Маленький настоящий SQLite session: open → add/flush → commit либо rollback
  → close. Показать committed/failed/persisted состояния таблицей и повторный session.
  Связь с `backend-transaction-repository`; repository TODO остаётся нетронутым.
- [x] 3. Правильная teacher yield-fixture на другом route: setup → yield → teardown,
  свежий app, контекст TestClient, cleanup overrides и при ошибке.
  Затем существующий `backend-api-test-review`; не исправлять его за ученика.
- [x] 4. Продолжить `backend-analytics-sql`: EXPLAIN, один индекс, повторные замеры,
  одинаковые rows до/после, цена индекса. Визуал scan/lookup + небольшая таблица плана.
  Начать SQLite, отдельно явно проверять PostgreSQL; ускорение не гарантировано.
- [x] 5. Проверить invalid/valid, rollback и живую следующую сессию, fixture isolation
  при success/failure, SQL equality. Исполнять учебный пример отдельно от student solution.

**Выход:** четыре небольших разъяснения, реальные локальные demos, test evidence.
**Освоение:** предсказать путь отказа/cleanup и объяснить, почему SQL result неизменен.

<a id="r03"></a>

## R03 — Вводный Document Intelligence A1 и действующий CI

**Вход:** R01, Data/ML, `data-release-study`, `ml-tabular-study`,
`data-paired-model-comparison`, `ml-evaluation-case`; SQL-часть после R02.
**Места:** существующий `projects/document_intelligence_lab/README.md`;
предлагаемые новые `part_a1/README.md`, `part_a1/demo.py`, `part_a1/test_demo.py`,
`part_a1/exercise/` под ним; будущий `.github/workflows/ci.yml`.
Student contract окончательно согласовать при реализации, не копировать tabular study.

- [x] 1. Подготовить маленькие разрешённые нейтральные документы, source/license manifest,
  annotation guide с неоднозначностями, schema и fixed split. Переиспользовать release
  protocol; таблица accepted/review/rejected и схема происхождения строки.
- [x] 2. Полностью разобрать **маленькую демонстрацию**, отдельно поставить самостоятельное
  сравнение rules/classical на другом split/вариации. Готовые split, preprocessing,
  метрики, calibration/threshold, ошибки и uncertainty — ссылки, не новый курс.
  Визуалы: группы по split, confusion matrix, несколько карточек ошибок.
- [x] 3. Сохранить seed/config/data+split identity, fitted preprocessing+model,
  predictions, metrics, error categories; пересчитать метрики из predictions;
  reload в свежем процессе и новом каталоге, без перезаписи прежнего run.
- [x] 4. Подготовить CI: locked base install, tests, Ruff/format/mypy, автономный smoke;
  training offline job отдельно, без pretrained downloads. Объяснить job/exit status,
  зависимости проверки и отличие infrastructure pass от learner check.
  Визуал data+code+config → run → artifacts и ветви CI.
- [ ] 5. Локально проверить команды; после отдельного разрешения сохранить реальный
  hosted run и доказательство обнаружения намеренного дефекта в изолированной пробе.
  Без hosted run писать CI CONFIGURED/NOT_RUN, а не VERIFIED.

**Выход:** A1 contract/demo/tests, fixtures/manifest, workflow, журнал проверок.
**Освоение:** самостоятельно воспроизвести эксперимент, защитить split/метрику и
разобрать ошибки. Улучшение baseline не обязательный результат. A1 **не** закрывает
полную часть A, для которой нужны PyTorch/HF и R06.

<a id="r04"></a>

## R04 — CPU-сервис, контейнер и вводный tracking

**Вход:** A1 artifacts, backend/R02. **Места:** будущие
`projects/document_intelligence_lab/service/` и `tracking_intro/`, спецификации
`labs/05_model_serving/README.md`, `labs/06_ml_lifecycle/README.md` — ссылки без зачёта.
Переиспользовать `modules/02_python_backend/09_docker_delivery/` и
`production-artifact-manifest`, `production-request-metrics`, `production-rollout-decision`.

- [x] 1. Teacher API с отдельной toy model; learner подключает **свою** A1 модель.
  Теория: request → validation → тот же preprocessing → prediction + version.
  Проверки missing/incompatible artifact, invalid input, train/inference parity.
- [ ] 2. Контейнер и readiness: start → load → ready → stop, повторный запуск.
  Объяснить image/process/service, не дублировать Docker-урок. Реальный container
  smoke только явным запуском; mock не равен запущенному контейнеру.
- [x] 3. Два реальных локальных MLflow runs после отдельного opt-in install:
  params/metrics/tags против artifact bytes, location и version identity.
  Визуал две карточки run со ссылками на файлы; найти и восстановить один artifact.
  Выполнено в [runtime-продолжении](../../local-runtime-continuation.md): actual
  flavors/replay и восстановление exact bytes, не зачёт learner experiment.
- [x] 4. Контролируемый переход A → B → отказ → A; откат model **и** preprocessing.
  Сохранить timings/errors/memory с версиями; график из измерений и timeline recovery.
  Объяснить median/tail и предел маленькой нагрузки, не обещать production benchmark.

**Выход:** launch recipe, tests, container config, runs, minimal rollback runbook.
**Освоение:** найти несовместимый artifact и воспроизвести восстановление.
Это вводная интеграция CPU, не зачёт обязательного vLLM или полной lifecycle lab.

<a id="r05"></a>

## R05 — Одно облачное развёртывание с ограничением расходов

**Вход:** R04; до запуска выбрать один provider, регион/данные, credentials,
максимальный бюджет и порядок удаления ресурсов вместе с пользователем.
**Место:** будущая `projects/document_intelligence_lab/deployment/`;
общие выводы переиспользуются R09, не второй deployment-проект.

- [x] 1. Подготовить русское объяснение object storage, service identity, минимальных
  прав, secret injection, закрытого/публичного доступа, health/logs и расходов.
  Визуал request → service → model artifact и отдельная граница секретов/прав.
- [ ] 2. Для выбранного провайдера дать пошаговый launch/smoke/observe/rollback/cleanup
  с явными resource names; точные команды проверять по актуальной документации.
  Не добавлять Terraform/Kubernetes ради единственного сервиса.
- [ ] 3. После разрешения выполнить реальный deploy/restart/rollback и проверить
  cleanup и прекращение расходов. Сохранить sanitized evidence без ключей и PII.

**Выход:** воспроизводимая инструкция и реальные логи одного deployment.
**Освоение:** объяснить права и стоимость, восстановить сервис и убрать его ресурсы.
Локальный Docker — не cloud evidence. До согласования внешнего запуска **NOT_RUN**;
можно продолжать локальные R06–R08, не объявляя R05 завершённым.

<a id="r06"></a>

## R06 — Полная часть A: перенос готовых PyTorch/HF знаний

**Вход:** R03 + существующие `lab-pytorch`, `lab-huggingface`,
`lab-training-resume`, `lab-training-diagnostics`, `lab-attention-mechanics`.
**Места:** `projects/document_intelligence_lab/README.md`, будущая `part_a/`;
в labs 01/02 добавлять только навигацию/необходимые обнаруженные исправления.

- [x] 1. Связать toy mechanics → pretrained experiment → самостоятельный classifier.
  Теорию lifecycle/autograd/attention не писать заново; компактная схема
  tokenizer → batch shapes/mask → encoder → classifier → held-out outputs.
- [x] 2. Объяснить протокол сравнения rules/classical/encoder на том же evaluation;
  замороженный encoder и adaptation различать по существующей HF-теории.
  Student эксперимент, конфиги/предсказания/отчёт не заполнять.
- [x] 3. Подготовить явный preflight: version/seed/revision/dataset/split, выбранный
  CPU/GPU profile и budget. Pretrained assets только explicit download; GPU
  optional для этой lab, CPU smoke не доказательство CUDA или качества модели.
  [Локальная input-проверка](../../../projects/document_intelligence_lab/part_a/README.md#предварительная-проверка-входов--без-обучения)
  не выполняет модель: device/seed/budgets записываются как requested settings.
  Проверка actual CUDA, ресурсного бюджета и pretrained обучения остаётся NOT_RUN.
- [ ] 4. Проверить teacher reload/parity и offline protocol tests, отдельно записать
  фактические pretrained results только после разрешённого запуска. Прогноз формы,
  карточка ошибки и learning curve с provenance; случайная модель — лишь mechanics.

**Выход:** подготовленная полная часть A и сравнимые artifact contracts.
**Освоение:** ученик объясняет различия ошибок/затрат и защищает собственную оценку;
низкое качество или отсутствие выигрыша допустимы при корректном исследовании.

<a id="r07"></a>

## R07 — Real embeddings, Qdrant и часть B: настоящий RAG

**Вход:** R06, modules 05/06, citations/ACL, experiment protocol.
**Места:** `labs/03_real_rag/README.md`; новые `theory.md`, `demo.py`,
`test_demo.py`, `tests/`, `exercise/` в этой lab; project `part_b/` хранит постановку
и learner artifacts, не дублирует реализацию lab.

- [ ] 1. Разрешённый corpus snapshot + manifest → chunks/IDs/metadata → реальные
  embeddings → постоянный Qdrant. Переиспользовать `rag-text-chunking`,
  `rag-index-sync`. Теория: semantic distance, normalized scores, metadata,
  index persistence; visual со shapes и связью chunk → source. Restart test.
- [ ] 2. Зафиксировать queries/relevance judgments независимо от найденных ответов;
  сравнить lexical и embedding retrieval. Переиспользовать `rag-ranking-study`;
  показать два top-k списка, per-query error и Recall/MRR/nDCG по постановке.
  Hybrid/reranker добавлять только как обоснованный измеренный опыт.
- [ ] 3. Явно выбрать generator/provider; начать локальным HF при подходящих ресурсах,
  затем R08 заменяет runtime на vLLM. Claim → evidence/citation → answer/no-answer;
  отдельная answer rubric и ручная проверка, не одна оценка LLM judge.
  Переиспользовать `rag-citation-validation`, ошибки/таймауты из модуля 05.
- [ ] 4. Проверить update/delete, permissions **до** top-k, restart, отсутствие
  ответа, provider failure, `rag-retrieval-regression`. Разобрать prompt injection
  как недоверенные документы; наличие citation не доказывает истинность ответа.
  Визуал index before/after, trust boundary и таблица недоступных источников.

**Выход:** фиксированные fixtures, model/corpus/index manifests, persistent service
recipe, offline unit tests, explicit service/model smoke, отдельные retrieval/answer
reports, timings/cost. Каждая часть имеет teacher demo и другую learner variation.
**Освоение:** объяснить потерянный релевантный документ и неподдержанное утверждение,
обновить источник и перепроверить старые вопросы. На 8 GB embeddings и generation
сначала последовательно, Qdrant/малые embeddings можно CPU; никаких скрытых загрузок.
Идеи [Hub](../../ai-ml-extension-plan.md#hub-references) — ссылки/лицензированный reuse,
не импорт готового решения и не автоматическое подключение платных сервисов.

<a id="r08"></a>

## R08 — Обязательный vLLM в Linux на ограниченной памяти

**Вход:** R07 + backend, HF inference, module 08; LoRA не prerequisite.
**Места:** `labs/05_model_serving/README.md`; будущие `theory.md`, `demo_client.py`,
`test_demo_client.py`, `smoke/`, `experiments/`; отдельное Linux `environment/`
с lock/config, [compute guide](../../compute-guide.md#vllm-linux-route).

- [ ] 1. После разрешения подготовить Ubuntu 24.04/WSL2 и проверить GPU + tiny CUDA;
  либо согласовать native Linux host. WSL зависит от Windows host, vLLM процесс
  исполняется в Linux. Windows CPU `.venv-training` не переносить/переписывать.
  Объяснить runtime/driver/device, Blackwell compatibility; схема client/runtime/GPU.
- [ ] 2. Первый smoke Qwen3-0.6B; затем выбрать один из
  [двух дополнительных кандидатов](../../compute-guide.md#vllm-candidates):
  Qwen2.5-1.5B-Instruct либо SmolLM2-1.7B-Instruct. Проверить точную revision,
  license/size, явно скачать, запустить **локальный snapshot** на loopback.
  Начать context 1024, one sequence, eager FP16 по ещё не испытанному профилю.
- [ ] 3. Разобрать weights/activations/KV, prefill/decode, token counts, dtype и
  отличие quantization от сокращения контекста. Visual: память по компонентам,
  request → queue → prefill → decode; временная шкала первого/следующих токенов.
  Teacher streaming client; learner variation на cancellation/deadline/ограничении
  очереди и bounded retries: не повторять бесконечно уже начатый ответ.
  Client fakes проверяют contract, но не реальный vLLM.
- [ ] 4. Реальный API/streaming → bounded concurrency 1 и 2 → restart с тем же
  snapshot. Измерить TTFT, token rate, E2E latency, throughput, errors, memory;
  сохранить cold/warm, prompt/output limits, версии и raw measurements.
  Concurrency 2 может не поместиться — зафиксировать безопасное отклонение перегрузки,
  не повышать предел вслепую. Повторить независимую answer evaluation R07.

**Выход:** отдельное serving environment, конфиг/клиент, GPU/runtime evidence,
измерения и графики из них, воспроизводимый restart. **Освоение:** объяснить цену
длинного контекста, остановить запрос, найти причину ошибки и восстановить сервер.
Ollama/HF не заменяют vLLM. В документации явно различать поддерживаемую архитектуру,
реальный smoke на этой GPU и качество модели. Все три модели скачивать не обязательно.

<a id="r09"></a>

## R09 — Полный lifecycle: данные, tracking, наблюдение и recovery

**Вход:** обе модельные labs, R08 и module 08; reuse R03/R04/R05 artifacts,
`data-release-study` и SQL/CSV versioning. **Места:** `labs/06_ml_lifecycle/README.md`,
будущие `theory.md`, `demo.py`, `test_demo.py`, `tests/`, `exercise/`, `runbooks/`.

- [ ] 1. Воспроизводимая memory-aware подготовка: schema/annotation/provenance,
  bounded batches, повтор без дублей, split identity, train/inference parity.
  Ссылки на готовые stream/release; схема row → batch → dataset version → model.
- [ ] 2. Развить реальный MLflow из R04: runs, artifact storage, registry и release
  manifest связывают data/config/code/model/preprocessing/index. Показать различие
  между метаданными и доступными bytes; восстановить artifacts в новой папке.
- [ ] 3. Реальные telemetry/logs, data drift против concept drift и delayed labels;
  ground-truth quality отдельно от proxy. Графики distributions и quality во времени
  с подписями «измерено»/«учебный сценарий»; alert не равен команде retrain.
- [ ] 4. Human-controlled promotion, shadow/canary, совместимый rollback model +
  preprocessing/index, recovery после сбоя, CI/deployment smoke, incident review.
  Visual release A → B → degrade → A; независимые checks version/parity/recovery.

**Выход:** pipeline/registry/monitoring recipe, сохранённые версии и runs,
promotion policy, rollback/runbook, incident evidence. **Освоение:** воспроизвести
сбой, отличить проблему данных от отсутствия labels и обосновать действие.
Не строить платформу: Kubernetes/Terraform/Spark/Airflow не prerequisites.
R04 introduction и теоретический module 08 не засчитывают этот реальный lifecycle.

<a id="r10"></a>

## R10 — Интеграция и защита Document Intelligence

**Вход:** R06–R09, готовый bounded workflow module 07; R05 evidence при облачном
варианте, иначе cloud остаётся незавершённым. **Места:** существующий project README,
будущие `architecture.md`, `defense-template.md`, `tests/`; отчёт пишет ученик.

- [x] 1. Связать части A/B и ограниченный workflow без дублирования lab code.
  Теория выбора rules/classical/encoder/RAG/finetuning, batch/online/API/self-hosted;
  reuse `production-product-study`. Diagram компонентов, trust boundaries и
  таблица «ограничение → решение → отвергнутая сложность».
- [x] 2. Подготовить разные acceptance сценарии: classification errors, no-answer,
  ACL, stale/delete, provider outage, restart/rollback, resource budget.
  Два независимых evaluation protocol, не единый «AI accuracy score».
- [x] 3. Дать пустую структуру защиты: проблема → данные → baseline → результаты →
  ограничения → стоимость/память → решение. Ученик отвечает на новую вариацию
  требования, сам разбирает ошибки и объясняет, что система не гарантирует.

**Выход:** единая навигация/контракты/teacher integration smoke и рубрика защиты,
а не заполненный портфель ученика. **Освоение:** независимая содержательная защита
по [существующей рубрике](../../project-defense.md). Наличие JSON/hashes, зелёный
pytest и красивые схемы не доказывают качество или честность эксперимента.

<a id="r11"></a>

## R11 — Выбранная ML-DEPTH: SFT, LoRA и условный QLoRA

**Вход:** основной маршрут, обе модельные labs, held-out protocol и выбранная
маленькая совместимая модель. **Места:** `labs/04_llm_finetuning/README.md`, будущие
`theory.md`, `demo.py`, `test_demo.py`, `tests/`, `exercise/`, отдельный opt-in stack.

- [x] 1. Объяснить когда менять prompt, retrieval или weights; фиксированная baseline
  evaluation, разрешённый dataset, chat template, split, loss masking/packing.
  Visual tokens/labels/mask, отдельно train и evaluation пути; не готовый learner SFT.
- [x] 2. Полностью разобрать tiny offline teacher LoRA mechanism: frozen weights +
  две low-rank матрицы, shapes/trainable parameters; связать с готовым autograd.
- [ ] 3. После явной загрузки/запуска: самостоятельное baseline → prompting → adapter
  comparison, сохранение/reload, формат/ошибки/деградации/ресурсы на тех же условиях.
  Графики quality/time/memory из реальных runs; loss alone не критерий done.
- [ ] 4. QLoRA выделить отдельным compatibility/memory experiment. Сначала проверить
  GPU/backend/формат и budget; RTX 5060 8 GB не гарантия. Если не подходит, сохранить
  обоснованное ограничение, не начинать платную аренду автоматически.

**Выход:** SFT contracts, teacher mechanism, adapter/reload recipe, tests и пустой
evaluation template. **Освоение:** объяснить что адаптер меняет и где ухудшает ответы.
DPO/RLHF/GRPO и большая LLM с нуля не добавляются в обязательный объём.

<a id="r12"></a>

## R12 — Пути и варианты специализаций

R12 — только навигатор: ниже перечислены варианты продолжения, их prerequisites
и место в программе. Новые уроки, лабораторные, зависимости и задания в этом пакете
не создаются. Выбирать специализацию сейчас не обязательно.

Общая база остаётся прежней: Python → данные и статистика → classical ML →
PyTorch/Hugging Face → оценка качества и эксплуатационные основы.
Далее выбирайте направление по типу задач, которые хочется решать:

| Направление | Что будете решать | Путь через существующую программу |
| --- | --- | --- |
| Табличное ML и прикладная аналитика | Прогноз числовых показателей, классификация, сравнение решений на структурированных данных | Modules 03–04 → `ml-tabular-study` → `ml-evaluation-case` → R03 → R04/R09 |
| AI Engineering и RAG | Поиск по документам, ответы с источниками, управляемые AI-процессы | HF lab → Modules 05–07 → R07 → обязательный базовый vLLM R08 → R10 |
| ML Engineering и адаптация моделей | Обучение, диагностика и адаптация модели под конкретную задачу | Training bridge → PyTorch/HF → resume/diagnostics → R06 → R09 → при необходимости R11 |
| Высокопроизводительный inference | Обслуживание моделей с ограничениями по памяти, задержке и нагрузке | Module 08 → базовый vLLM R08 → углублённые batching, KV cache и измерения |
| Data Engineering для ML | Подготовка и восстановление данных, воспроизводимые загрузки и пересчёты | Module 03 → `python-paged-stream` → `data-release-study` → R09 → recovery/backfill |
| Computer Vision, OCR и multimodal | Изображения, сканы и документы, где одного готового текста недостаточно | PyTorch/HF → оценка качества → R10 → отдельная профильная работа с разрешёнными изображениями |
| Speech и ASR | Распознавание речи и анализ аудио | PyTorch/HF → оценка качества → отдельная профильная работа с разрешёнными аудиозаписями |
| Временные ряды | Прогноз по времени с проверкой на будущих периодах | Module 04 → `ml-forecasting-intro` → temporal backtesting и разбор ошибок по горизонту |
| Ranking и рекомендации | Упорядочивание результатов поиска и подбор релевантных объектов | Retrieval/evaluation → `rag-ranking-study` → R07 → отдельная работа с judgments и sampling |
| ML Platform и MLOps | Доставка, наблюдение, воспроизведение и восстановление модельных систем | Module 02 + Module 08 → R04 → R09 → recovery/deployment под конкретную потребность |

Не нужно проходить все ветки. Если интереснее работа с документами — начните с
AI Engineering/RAG; если обучение и поведение модели — с ML Engineering; если
данные и проверяемые прогнозы — с табличного ML. CV, speech, time series и ranking
имеет смысл выбирать после появления конкретной задачи и подходящих данных.

Базовый **vLLM остаётся обязательным R08**, а его глубокая оптимизация — отдельным
вариантом специализации. Для RTX 5060 Laptop сверяйтесь с
[ресурсным профилем и Linux-маршрутом](../../compute-guide.md#rtx5060-profile):
наличие GPU не гарантирует, что любая модель или способ адаптации поместится в память.

Специализации здесь — **OPTIONAL / не реализованы как отдельные курсы**.
Их перечисление не меняет progress и не добавляет обязательных зачётов.

## Карта согласованных коротких блоков → пакеты

| Ранее согласованный набор | Где теперь реализуется |
| --- | --- |
| Этап 1: mutable defaults/traceback, свои tests, word index, decomposition/review | R01; defaults/word index уже существуют, дополнять только новые умения |
| Этап 2: data release, SQL index, baseline comparison, reproduction/CI | R02 SQL + R03; готовые data/ML studies как prerequisites |
| Этап 3: API, container, два runs, rollback; отдельно cloud | R04 + R05; полное развитие в R09 |
| Этап 4: persistent index, два retrieval, grounded/no-answer, update/ACL | R07 → интеграция R10 |
| Обязательный vLLM: CUDA, server, client, measurements/restart | R08; две дополнительные модели — кандидаты, не три обязательных загрузки |
| Этап 5: LoRA, advanced vLLM, recovery/backfill, одна модальность | R11 либо выбранная R12; не четыре обязательные специализации |
| Полные tracking/lifecycle и Document Intelligence | R09/R10; A1/CPU smoke не сокращают их prerequisites |

## Как принимать каждый реализованный пакет

Четыре независимых вида свидетельств:

| Проверка | Что доказывает | Что не доказывает |
| --- | --- | --- |
| Unit / teacher tests | Контракт маленького механизма, значения/ошибки | Самостоятельность ученика и качество модели |
| Integration / smoke | Реальный pipeline/API/reload/service/device работает в записанной среде | Обобщение на новые данные и production устойчивость |
| ML evaluation | Результат на фиксированной независимой оценке с artifacts | Автоматический перенос на иной домен/язык/нагрузку |
| Вариация и защита | Ученик объясняет решения/ошибки и применяет механизм | Не заменяется структурной проверкой отчёта |

Перед пакетом повторно сверить локальные изменения, выбранные файлы и prerequisites.
Новые tests должны обнаруживать намеренно неверное teacher-поведение, но не трогать
learner code ради демонстрации красного теста. Для новых ID проверить scoped `test/check`
и отсутствие обязательных skip/xfail в зачёте; ручную оценку честно оставить REQUIRES_REVIEW.

Команды ниже — **будущая приёмка реализации**, а не утверждение, что она уже проведена.
Из корня проекта, после отдельно подготовленного соответствующего окружения:

```powershell
.venv/Scripts/python.exe -m pytest tests/integration/test_markdown_links.py tests/tooling/test_documentation.py -q
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy
.venv-training/Scripts/python.exe -m pytest labs
.venv-training/Scripts/python.exe -m mypy -p labs
```

Дополнительно выбранные teacher demos/unit tests пакета, явные optional-live/GPU
smoke только с разрешением; обычный pytest остаётся offline. При добавлении группы
проверить locked base install отдельно от opt-in install, не смешивать Linux serving
и Windows CPU training. Полный regression запускать после согласованного набора кода;
docs-only уточнение не объявлять доказательством готовности будущего runtime.

Локальные links/anchors проверять и для новых **untracked** Markdown, которые старый
tracked-only link test ещё не охватывает. Диаграммы сопоставить с demo-значениями;
открыть rendered Markdown/SVG/PNG, указать просмотренные файлы и реальные ограничения.
Если визуальный просмотр не состоялся — NOT_VERIFIED, не «отображение проверено».
Report каждого пакета: изменённые файлы, команды/exit codes/counts, среда,
технически проверено / model runs NOT_RUN / учеником REQUIRES_REVIEW.

## Следующий шаг

Локальные материалы подготовлены; следующие действия — **явные runtime-эксперименты**
R03–R11 в границах таблицы статусов, а не повторная реализация прежних уроков.
Ученик проходит материалы после их prerequisites. Выбор cloud provider и Linux setup
остаётся перед внешним запуском; это не причина блокировать локальные объяснения
и маленькие практикумы. R12 ограничен путями специализации и не требует выбора
или реализации профильной ветки в текущей работе.
Сам план не даёт разрешения на установки, внешний запуск или публикацию.

## Проверено при подготовке самого плана

11.10.2026, Windows / существующая `.venv`, только документационные изменения:

- `.venv/Scripts/python.exe -m pytest tests/integration/test_markdown_links.py tests/tooling/test_documentation.py -q`
  — **13 passed**, exit 0.
- `git diff --check` — exit 0, замечаний нет.
- Дополнительный разовый вызов существующего `broken_local_links` для всех
  tracked/untracked Markdown: **268 файлов, 0 broken**. Отдельно сопоставлены
  **36 ссылок с якорями** в изменённых документах с явными ID/разобранными заголовками.
  Первая вспомогательная проверка ошибочно требовала только явный `id`; после
  учёта обычных Markdown-заголовков завершилась успешно, сами уроки не менялись.
- Mistune разбор нового плана: **5 таблиц, 48 checklist items**, 12 якорей пакетов;
  code fences сбалансированы. Это структурная проверка, **не** визуальный просмотр.
- Арифметика иллюстрации KV cache в compute guide: **28 / 192 MiB**;
  это модельный расчёт, не измерение vLLM.
- SHA-256 сверка исходных 902 tracked/untracked файлов: изменены только шесть
  документов навигации/плана, **896 прежних файлов побайтно сохранены**, удалений нет;
  добавлен этот план. Progress, learner code, curriculum, CLI, зависимости/lock
  не менялись. HEAD/ветка сохранены.

Не проводились: полный regression, Ruff/mypy (исполняемый код не изменялся),
визуальный просмотр Markdown в браузере, новые model/dataset downloads, Linux/GPU/
vLLM tests, CI/cloud runs. Они не объявляются успешными. План не меняет статусы
ученических заданий и не свидетельствует о выполнении будущих пакетов.
