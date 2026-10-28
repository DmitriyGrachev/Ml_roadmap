# Теоретический пакет 7 — Agents/workflows → Production AI

Репозиторий: `C:\ProjectsDirectory\AIML\_road`, ветка `codex/ai-ml-wave1`,
HEAD `836028944eceaa260cb47d0056b593af4a4648d4`. Дата: 04.10.2026.
Пакет углубляет существующие Module 07/08, не создаёт новый курс или live lab.

Материалы подготовлены, локальная механика технически проверена.
Итоговое независимое review завершено: замечания исправлены и повторно проверены.
Manifest дополнен по замечанию; адресные проверки и повторная полная регрессия
пройдены на исправленном коде.
Понимание ученика не проверено и progress за него не изменяется.

## С чего начинать и как проходить

Первым откройте [Module 07 README](../modules/07_agents/README.md).
Сохраняются прежние prerequisites: LLM Engineering и RAG, типизированные
границы, validation, Python collections и evaluation.

1. Уроки Agents 01–02: сначала спрогнозируйте переход и разрешение вызова,
   затем прочитайте разбор фиксированного сценария велосервиса.
2. Уроки 03–04: сравните ошибку до действия и потерянный ответ после него,
   проследите бюджеты, подтверждение и восстановление сохранённого состояния.
3. Уроки 05–06: запустите прежний локальный LangGraph/MCP example и отделите
   protocol/orchestration от разрешений и оценки полезности.
4. Выполняйте самостоятельные задания по ссылкам уроков. Teacher trace —
   не ваше решение и не доказательство усвоения.
5. Затем [Module 08 README](../modules/08_production_ai/README.md) и уроки 01–06:
   контракт/готовность → версия/протокол сравнения → наблюдение → бюджеты →
   границы данных → выпуск/инцидент.
6. Для ручных вариаций предложите собственные проверки, решение и ограничения.
   После своей реализации запускайте прежний строгий `check ID`.

Две преподавательские демонстрации, после чтения соответствующей части:

```powershell
Set-Location C:\ProjectsDirectory\AIML\_road
.venv/Scripts/python.exe -m modules.07_agents.walkthrough --output generated-reports/my-workflow-01
.venv/Scripts/python.exe -m modules.08_production_ai.walkthrough --output-dir generated-reports/my-production-01
```

При повторе выбирайте **новое имя каталога**: даже существующая пустая папка
отклоняется. Выходы не пишутся в learner submissions. Обе команды офлайн и не
скачивают модели/датасеты. Учебный in-process framework запускается прежней командой
`.venv/Scripts/python.exe modules/07_agents/05_langgraph_mcp/example.py`.

Команды проверки собственных работ (из корня репозитория):

```powershell
Set-Location C:\ProjectsDirectory\AIML\_road
.venv/Scripts/python.exe scripts/learn.py test agents-tool-dispatch
.venv/Scripts/python.exe scripts/learn.py check agents-tool-dispatch
.venv/Scripts/python.exe scripts/learn.py test production-release-gate
.venv/Scripts/python.exe scripts/learn.py check production-release-gate
```

`test` допускает ожидаемо невыполненные задания; `check ID` проверяет конкретную
ученическую работу без обязательных xfail/skip. Новый author QA не расширяет
контракты старых заданий. За ученика `check` не выполняется.

## Архитектурные решения и файлы

README остаются входными точками; рядом с шестью уроками каждого модуля добавлена
русская теория. Небольшие таблицы переходов, traces и timeline показывают
наблюдаемые данные, а не внутренние рассуждения модели. Notebook, графическая
библиотека и новый frontend здесь не нужны.

Один нейтральный сценарий продолжает G-01 пакета 6: ночного хранения нет,
забрать велосипед нужно до 19:00. Предложения модели заранее написаны автором;
действие с последствиями только имитируется. Часть Б использует события части А.
Это не универсальный agent engine и не решение generic student dispatcher,
checkpoint, metrics, release gate или открытого `production-product-study`.

Новые файлы:

- Agents: [01 theory](../modules/07_agents/01_workflows_state/theory.md),
  [02](../modules/07_agents/02_tools_permissions/theory.md),
  [03](../modules/07_agents/03_bounded_agents/theory.md),
  [04](../modules/07_agents/04_checkpoints_approvals/theory.md),
  [05](../modules/07_agents/05_langgraph_mcp/theory.md),
  [06](../modules/07_agents/06_evaluation_handoffs/theory.md).
- Production: [01 theory](../modules/08_production_ai/01_serving_contracts/theory.md),
  [02](../modules/08_production_ai/02_releases_evaluation/theory.md),
  [03](../modules/08_production_ai/03_observability/theory.md),
  [04](../modules/08_production_ai/04_budgets_resilience/theory.md),
  [05](../modules/08_production_ai/05_privacy_security/theory.md),
  [06](../modules/08_production_ai/06_rollout_incidents/theory.md).
- [Agents walkthrough](../modules/07_agents/walkthrough.py) и
  [Production walkthrough](../modules/08_production_ai/walkthrough.py).
- [Agents author tests](../tests/integration/test_packet7_agents.py) и
  [Production author tests](../tests/integration/test_packet7_production.py).
- Этот единый отчёт. История [карты покрытия](wave2-coverage.md#theory-packet-7)
  дополнена, а не заменена; 14 README получают навигацию.

## Реальные проверки

Базовое окружение: Python 3.12.14; LangGraph 1.2.12, MCP 2.2.0,
LangSmith 0.14.0, FastAPI 0.141.1, Starlette 1.6.0, Pydantic 2.13.5,
AnyIO 4.15.1, pytest 9.1.1, Ruff 0.16.8, mypy 2.3.1.
Фактический `find_spec` подтвердил отсутствие torch, transformers и matplotlib
в base: преподавательские сценарии не требуют `training` или `visualization`.

До изменений: `.venv/Scripts/python.exe -m pytest -q` → **998 passed,
50 skipped, 1160 xfailed**, 114.40 s, exit 0. Одно прежнее предупреждение
Starlette об устаревающем AnyIO `BlockingPortal`; оно не подавляется.
Исходный связанный прогон Modules 07/08 и author tests пакета 6:
**97 passed, 314 xfailed**, 12.26 s, то же предупреждение.

`uv sync --locked --offline --dry-run` → exit 0, 199 packages resolved,
156 checked, **Would make no changes**. Это проверка текущего окружения,
не новая чистая установка. Новые зависимости не требуются.

### Часть А перед реализацией Б

| Команда | Результат |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/integration/test_packet7_agents.py modules/07_agents -q` | После исправления policy boundary: 40 passed, 128 xfailed, повтор контроллера 2.88 s |
| `.venv/Scripts/python.exe -m mypy -p modules.07_agents` | Success, 45 source files |
| `.venv/Scripts/python.exe modules/07_agents/05_langgraph_mcp/example.py` | `astronomy`, tool `lookup_exhibit`, capability True, результат `Brass telescope`; exit 0 |
| `.venv/Scripts/python.exe modules/08_production_ai/01_serving_contracts/example.py` | in-process: release v1; после drain live 200, ready 503; после shutdown closed True; exit 0 |

Контроллер запустил новую демонстрацию отдельно:

```powershell
.venv/Scripts/python.exe -m modules.07_agents.walkthrough --output generated-reports/teacher-packet7-a-verified-01
```

14 случаев сохранены в `trace.json`; отдельный `checkpoint.json` содержит
ожидающее подтверждение состояние. SHA-256 трассы совпал с запуском разработчика:
`52FF2F7EE918F4DF94CE7791D2A1E2B44E0E01E2084C810D94F87E229C89343D`.
Симулируемое время не является измерением задержки настоящего инструмента.

| Случай | Исход | Шаги / попытки / условные ms / effects |
| --- | --- | --- |
| answer | answered, без предложения действия | 1 / 0 / 10 / 0 |
| success | reminder_recorded | 2 / 1 / 20 / 1 |
| waiting | awaiting_confirmation | 1 / 0 / 10 / 0 |
| denied, invalid, refused, cancelled, changed_args | соответствующий отказ до действия | 1 / 0 / 10 / 0 |
| failure_recovered | reminder_recorded | 3 / 2 / 30 / 1 |
| attempt_exhausted | attempt_limit | 2 / 1 / 20 / 0 |
| known_replay | reminder_recorded, без второго эффекта | 2 / 1 / 20 / 1 |
| unknown_after_effect | unknown_needs_reconciliation | 2 / 1 / 20 / 1 |
| step_limit, time_limit | соответствующий предел | 1 / 0 / 10 / 0 |

`effects` известен преподавательскому симулятору; настоящий клиент при потере
ответа не знает это значение без reconciliation. Локальный checkpoint не
удостоверяет происхождение данных, внешнее exactly-once или конкурентную запись.

Независимое ревью А нашло возможность повысить лимиты внутри сохранённого JSON.
Три регрессионных случая сначала воспроизвели ошибку, затем прошли после введения
независимой `RunPolicy` приложения при каждом resume. Нельзя строить эту политику
из того же недоверенного checkpoint. Уточнены точные причины остановки в тестах.
Повторный A02 trace совпал с A01; API `build_demo()` и числа выше не изменились.
Повторное независимое ревью подтвердило оба исправления без новых замечаний;
это чтение кода и журналов, не повторный запуск suite рецензентом. Часть Б начата
только после этого этапа. Приведённый повтор тестов выполнен контроллером.

### Связанная часть Б и регрессия

Контроллер отдельно выполнил:

```powershell
.venv/Scripts/python.exe -m modules.08_production_ai.walkthrough --output-dir generated-reports/teacher-packet7-b-verified-02
.venv/Scripts/python.exe -m pytest tests/integration/test_packet7_agents.py tests/integration/test_packet7_production.py modules/07_agents modules/08_production_ai tests/integration/test_markdown_links.py -q
```

Связанный прогон: **96 passed, 314 xfailed**, 5.78 s, одно прежнее предупреждение
Starlette. Из успешных случаев **24 — новые author tests** (17 Agents, 7 Production),
не дополнительные требования старого `check`. Самостоятельные TODO не решались.

Пять сохранённых JSON (`observed_events`, `manifest`, `window_metrics`,
`candidate_decisions`, `incident`) побайтно совпали с отдельным исправленным
запуском разработчика B02. Ранний B01 сохранён как история, но не используется
как актуальный manifest. Имена новых каталогов исключают перезапись старых выходов.
Окно — именно восемь именованных случаев А, а не все 14 и не поток пользователей:

- Технически успешны 3/8, технические ошибки 2/8; cancel, refuse и permission
  denial — по 1/8. Разрешённый отказ не записан как ошибка инструмента.
- Условные задержки: `[10,10,10,10,20,20,20,30]`; nearest-rank p95 имеет ранг
  `ceil(0.95×8)=8` и равен 30 ms. Это не измерение реальной нагрузки.
- 7 авторских предложений, 5 имитированных попыток инструмента, **0 реальных
  вызовов модели**. По учебной ставке 2 credits/attempt расход `5×2=10` из 16,
  остаток 6. Это не тариф провайдера. Арифметика отдельно пересчитана контроллером.
- Полученных live-меток нет: знаменатель 0, `live_quality_rate=null`, а не 100%
  успеха. Четыре авторские парные метки для release illustration — другой набор
  свидетельств, не измерение обобщения на действительно незнакомых данных.

Кандидат с критической ошибкой отклонён (`reject`), без обязательной метки —
`hold_insufficient_evidence`, совместимый полный fixture — `locally_eligible`,
несовместимый rollback — `block_incompatible`. Критерии фиксированы до результатов.
Это локальные решения на авторских данных, не выпуск в production.

В инциденте `response_lost` привилегированный симулятор показывает effects=1,
receipt отсутствует. В рамках fixture это исключает ошибку до эффекта; выбран
запрет автоматического повтора и ожидание authoritative reconciliation. Локальная
последующая проверка сохраняет attempts=1/effects=1; реальное внешнее восстановление
не выполнялось. Короткий runbook отделён от самостоятельной вариации.

| Конечная команда | Результат |
| --- | --- |
| `.venv/Scripts/python.exe -m ruff check .` | All checks passed |
| `.venv/Scripts/python.exe -m ruff format --check .` | 859 files already formatted |
| `.venv/Scripts/python.exe -m mypy` | Success, 631 source files |
| `.venv/Scripts/python.exe -m pytest -q` | После исправления manifest: 1022 passed, 50 skipped, 1160 xfailed, 1 прежний warning; 94.47 s |

Итоговое независимое review: **завершено, открытых замечаний нет**. Рецензент
прочитал весь пакет изменений, требования и сохранённые артефакты, но не повторял
suite: результаты команд выше получены контроллером. Существенных проблем не
найдено; единственное небольшое замечание — команда первого запуска ссылалась
на уже существующий teacher output. Она исправлена на свободный путь
`generated-reports/my-workflow-theory-01`; отдельное повторное review подтвердило
исправление и сохранность требования нового каталога. После этой правки только
документации повторены Markdown QA и проверка сохранности; Python-код не менялся,
полная регрессия повторно не запускалась.

Skip/xfail не выдаются за прохождение ученических работ; их числа совпадают
с исходной регрессией. Все новые author
tests прошли. Ранний полный прогон до исправления manifest дал 1020 passed,
50 skipped, 1160 xfailed, 1 прежний warning за 100.10 s; это исторический результат,
не замена повторному конечному прогону.

Ревью Б обнаружило неполную identity в manifest: нужны также код сравнения,
авторские input/label fixtures и runtime/dependency identity. Добавлены реальные
SHA-256 кода A/B/rollback, точных выбранных A cases, schema/window IDs,
baseline/candidate evidence, протокола, `pyproject.toml` и `uv.lock`; записаны
установленные версии Python и используемого окружения. Изменение копии latency
или candidate label меняет соответствующий digest — проверено отдельными тестами.
Факты инцидента также извлекаются из A case, а не дублируются строковыми константами.
Три новые регрессионные проверки сначала воспроизвели пробел, затем прошли;
Повторное независимое review подтвердило оба исправления без новых существенных
замечаний; оно читало код, сохранённые артефакты и журналы, suite не повторяло.
Порядок критерии → исходы задаётся устройством
учебного примера; отдельная историческая preregistration исследования не
проводилась и не заявляется. Это не эксперимент с невиданными заранее данными.

### Текст, ссылки, схемы и первичные источники

Отдельная проверка охватила **28 документов**: 12 теорий, 14 README, новый раздел
карты и отчёт. Проверены 183 локальные ссылки, один якорь, 21 таблица и 19 fenced
блоков: цели существуют, якорь найден, fences закрыты, число столбцов согласовано.
Проверка использовала существующую библиотеку Mistune для локального HTML;
новый dependency не добавлялся. Это структурная проверка отображения, а не
визуальный просмотр в браузере или гарантия всех Markdown-редакторов; такой
просмотр **NOT_RUN**, веб-сервер не запускался.

Таблицы переходов сопоставлены с 14 сохранёнными случаями А, таблица окна —
с восемью выбранными событиями, решения и timeline — с JSON части Б. ASCII
схемы canary/shadow являются объяснением архитектуры, не trace работающего rollout.
Сохранённые артефакты преподавателя отделены от submissions и не перезаписаны.

Ссылки открыты и сверены по первичным материалам: LangGraph Graph API,
persistence/interrupts, MCP Python SDK client и раздел Tools протокола,
LangSmith tracing context, FastAPI lifespan, scikit-learn model persistence,
OpenTelemetry signals/sensitive data, Google ML monitoring и главы Google SRE
о SLO, overload, cascading failures, canary и postmortem. В теориях названы
конкретные разделы и цель чтения; чтение документации не запускало её примеры.
Фактические LangGraph/MCP/FastAPI APIs дополнительно проверены установленными
локальными примерами и тестами, а не только текущей веб-документацией.

### Сохранность рабочей копии

Сверка SHA-256 с начальным снимком **885 файлов**: изменены только 15 прежних
файлов — 14 README и карта покрытия; остальные **870 совпадают**, удалений нет.
Новых файлов пакета **17**, перечислены выше. Student TODO, пользовательские
реализации/отчёты, старые examples/tests, curriculum/CLI, зависимости и lock,
пакеты 1–6 сохранены. Хеш `progress.md` остался:
`9C78D95D05EFB7234C8B3412D072577916A11192531AEE1B27A0DF60CE647DC0`.
HEAD/ветка не изменены. Установок, загрузок моделей/датасетов, внешних действий,
commit/push/merge нет. Временные teacher artifacts и материалы проверки оставлены
локально; они игнорируются Git и не являются выполненной ученической работой.

## Границы и следующие практические этапы

Локальная механика и проверка содержания урока отделены от самостоятельного
понимания: объяснение вариаций, TODO и защита решений — **REQUIRES_REVIEW**.
Внешние MCP endpoints/providers, настоящая LLM, distributed exactly-once,
нагрузочное испытание и deployment — **NOT_RUN / NOT_VERIFIED**.
Готовый JSON и успешный pytest не удостоверяют полезность или безопасность LLM.

Дополнительные training/visualization/GPU среды в этом пакете **NOT_RUN**:
их код не изменяется, новые уроки не требуют этих opt-in групп. Новая чистая
установка также **NOT_RUN**; выше указан offline dry-run существующего base.

После самостоятельного освоения модулей логично переходить к уже
запланированным этапам, соблюдая их собственные prerequisites:

1. [Real RAG](../labs/03_real_rag/README.md): реальные embeddings/index,
   retrieval и answer evaluation.
2. [Serving](../labs/05_model_serving/README.md) и
   [tracking/lifecycle](../labs/06_ml_lifecycle/README.md): реальные артефакты,
   воспроизводимые измерения, управляемый выпуск и мониторинг.
3. [Document Intelligence](../projects/document_intelligence_lab/README.md):
   связный capstone после необходимых лабораторных.

Все эти стадии сохраняют **PLANNED**. [SFT/PEFT](../labs/04_llm_finetuning/README.md)
остаётся отдельной веткой **ML-DEPTH · PLANNED**; fine-tuning не является
обязательным условием serving. vLLM остаётся OPTIONAL, QLoRA требует отдельной
проверки совместимости. Следующий пакет автоматически не запускается.
Commit/push/merge не выполняются.
