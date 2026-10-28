# Локальные runtime-эксперименты: MLflow, Qdrant и PEFT

Продолжение R04/R07/R09/R11 от 11.10.2026 после подготовки
[материалов R02–R12](remaining-roadmap-verification.md).
R12 остаётся [навигатором специализаций](superpowers/plans/2026-10-11-remaining-roadmap.md#r12).

Актуальное дополнение: [R07 MiniLM → локальный R09](#r07-r09-local) после явного
разрешения на модель. Ранние NOT_RUN ниже относятся к состоянию до этого разрешения;
generator по-прежнему согласуется отдельно, vLLM DEFERRED_ENV. Авторские результаты
не меняют student progress.

## Окружения и зависимости

Новые зависимости находятся только в opt-in группах, закреплены `uv.lock`.
Базовый `uv sync` сохраняет прежний состав. Действующие `.venv` и
`.venv-training` не синхронизировались поверх новых групп.

| Назначение | Группа | Отдельное окружение | Проверенные версии |
| --- | --- | --- | --- |
| Tracking и registry | `tracking` | `.venv-tracking` | MLflow 3.17.0 |
| Постоянный локальный vector index | `retrieval` | `.venv-rag` | qdrant-client 1.19.1 |
| Обучение LoRA adapter | `finetuning` (включает `training`) | `.venv-finetuning` | PEFT 0.21.2, accelerate 1.15.0, torch 2.14.0+cpu, transformers 5.17.0 |

Реальные установки выполнены из корня существующего проекта:

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-tracking'
uv sync --locked --group tracking
$env:UV_PROJECT_ENVIRONMENT = '.venv-rag'
uv sync --locked --group retrieval
$env:UV_PROJECT_ENVIRONMENT = '.venv-finetuning'
uv sync --locked --group finetuning
Remove-Item Env:UV_PROJECT_ENVIRONMENT
```

Все три установки завершились с exit 0. Это установка Python packages,
без загрузки моделей/датасетов или запуска сервера. Дополнительно создана
`.venv-base-check` обычной командой `uv sync --locked`: в ней отсутствуют torch,
transformers, datasets, MLflow, Qdrant, PEFT и Matplotlib. `uv pip check` для всех
четырёх окружений завершился успешно. Lock разрешает 241 package для всех групп;
это не означает их установку в базовую среду.

## Граница авторского эксперимента

Проверяются настоящие библиотеки и реальные сохранённые bytes. Маленькие author
fixtures и случайная модель позволяют проверить API, обучение и восстановление.
Они не оценивают качество pretrained модели на вашей задаче. Прежние упражнения,
их ID/контракты, реализации и progress сохраняются; самостоятельные отчёты
заполняются учеником.

## Что действительно выполнено

| Этап | Реальный опыт | Не подтверждает |
| --- | --- | --- |
| R04/R09 MLflow | Два sklearn runs, actual flavors и pyfunc, SQLite versions 1/2, alias 1→2→1; restore точных bytes и inference в новом процессе | Превосходство новой модели, hosted registry, автоматическое production promotion |
| R07 Qdrant | Local disk query, ACL до top-1, revoke/delete/revision replacement, close/reopen и отдельный process; сверены все ID, payload и vectors | Semantic retrieval, pretrained encoder, generator, server ANN/concurrency/crash recovery |
| R11 PEFT | Настоящий LoRA adapter на tiny random Llama из config; 24 AdamW steps, frozen base, safetensors save, exact fresh-process logits/predictions | Качество pretrained SFT, QLoRA/CUDA или точный training resume |

MLflow использует ранее подготовленные A1 data/splits: шесть test документов,
accuracy/macro-F1 = 1. Одинаковые ответы двух seed не доказывают rollback:
проверены разные model/flavor/bundle hashes и возврат именно version 1.
SQLite metadata без сохранённых artifacts недостаточно для inference.

Qdrant проверен на **ручных двумерных vectors**, не embeddings модели:
без ACL top-1 staff score=1; public top-1 SCAN≈0.993884. После revoke/delete и
замены HOURS осталось три актуальных points. Новый процесс проверяет полное
содержимое index, а не наличие его папки. При замене текста переиспользован
ручной vector: это mechanics, не production re-embedding.

PEFT: 448 trainable и 10144 frozen параметров; четыре LoRA tensors изменились,
base bytes не изменились, gradients frozen-параметров отсутствуют.
Train loss до steps 1/24: 2.537451→2.203713; validation 2.530804→2.388297;
test **2.562154→2.562948**, слегка хуже. Test ответы `amber`, `birch` вместо
`fern`, `grove` неверны. Падение train loss не означает освоение задачи моделью.
Проверена идентичность inference, не сохранение optimizer/RNG для resume.

Существующие локальные свидетельства (gitignored; не ученические отчёты):

- `artifacts/runtime-continuation-r04-v2/tracking.json`;
- `artifacts/runtime-continuation-r09-final/registry.json`;
- `artifacts/runtime-continuation-r09-final-restart/restart-verification.json`;
- `artifacts/r07-qdrant-20261011/mechanics-receipt.json` и `fresh-process-receipt.json`;
- `labs/04_llm_finetuning/artifacts/peft-author-02/report.json`, `identity.json`, `loss.svg`.

Каждый опыт сохраняет версии, параметры, identity данных/split/model и реальные
результаты. Это локальные receipts, не опубликованные в Git доказательства.
Первый registry receipt (`runtime-continuation-r09`) содержит source hash до
форматирования и последующего retry fix; он сохранён как исторический.
Новые `r09-final`/`r09-final-restart` созданы после форматирования окончательного
кода, registry source SHA256:
`7159668f58e2c69558ac1c306f681a2b2fc99c31fbdb338cd4be9a28e7544d50`.
Повторный lifecycle на тех же tracking inputs получает собственное новое имя;
прежние model versions/aliases и artifacts не сбрасываются. Partial failure
не fault-injected: это не transactional cleanup/crash recovery. Ранний
`runtime-continuation-r04` предшествует исправлению pyfunc signature/telemetry
и superseded файлом v2: network silence раннего запуска **не проверена**.
Текущий helper выключает MLflow telemetry до import; final integration tests
запрещают socket connect. Trusted pickle warning остаётся осмысленной границей:
только собственные operator-controlled artifacts. Generated flavor conda.yaml
не закрепляет pip; автоматическое создание serving environment не проверено.

## С чего начать и как повторить

Если вы начинаете с нуля, порядок не меняется:
[Environment](../modules/01_python_core/00_environment/README.md) →
[Object Model](../modules/01_python_core/01_object_model/README.md) → Collections
и прежние задания. Эти runtime-опыты идут **после prerequisites**, не вместо них.
Проверка старта из `C:/ProjectsDirectory/AIML/_road`:

```powershell
uv sync --locked
.venv/Scripts/python.exe scripts/learn.py validate-env
.venv/Scripts/python.exe scripts/learn.py list
```

Для подготовленного ученика: A1 → [tracking](../projects/document_intelligence_lab/tracking_intro/README.md)
→ [registry/restart](../projects/document_intelligence_lab/tracking_intro/registry-lifecycle.md).
После retrieval prerequisites — [Qdrant опыт](../labs/03_real_rag/runtime.md).
После PyTorch/HF — [LoRA теория и PEFT опыт](../labs/04_llm_finetuning/theory.md).
Каждая ссылка содержит разбор, прогноз, независимую вариацию и отдельный отчёт.

Команды повторения требуют **новых отсутствующих output-папок**:

```powershell
.venv-tracking/Scripts/python.exe -m projects.document_intelligence_lab.tracking_intro.demo --output artifacts/my-tracking-01
.venv-tracking/Scripts/python.exe -m projects.document_intelligence_lab.tracking_intro.registry --tracking artifacts/my-tracking-01 --output artifacts/my-registry-01
.venv-tracking/Scripts/python.exe -m projects.document_intelligence_lab.tracking_intro.registry --selected-config artifacts/my-registry-01/registry.json --output artifacts/my-registry-restart-01

$snapshotReceipt = .venv-rag/Scripts/python.exe -m labs.03_real_rag.dense hand-snapshot --output artifacts/my-hand-01 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'hand snapshot failed' }
.venv-rag/Scripts/python.exe -m labs.03_real_rag.dense qdrant-smoke --storage artifacts/my-qdrant-01 --snapshot artifacts/my-hand-01 --manifest-sha256 $snapshotReceipt.snapshot_sha256
if ($LASTEXITCODE -ne 0) { throw 'Qdrant smoke failed' }
.venv-rag/Scripts/python.exe -m labs.03_real_rag.dense qdrant-verify --storage artifacts/my-qdrant-01 --snapshot artifacts/my-hand-01 --manifest-sha256 $snapshotReceipt.snapshot_sha256 --receipt artifacts/my-qdrant-01/restart.json

.venv-finetuning/Scripts/python.exe -m labs.04_llm_finetuning.peft_demo --output artifacts/my-peft-01
.venv-finetuning/Scripts/python.exe -m labs.04_llm_finetuning.peft_demo --verify artifacts/my-peft-01
```

Не применяйте teacher mutations к своему production index. Hash проверяет
сохранность, не доверие к чужому файлу; folders должны принадлежать оператору
и не меняться конкурентно между проверкой и чтением.

## Техническая приёмка

Команды из корня; `pytest` означает проверку репозитория, не зачёт ученика.
Gated runtime tests используют настоящие библиотеки. Явный gate без dependency
даёт ошибку, не успешный skip; обычный pytest эти integrations не запускает.

| Команда | Наблюдённый результат |
| --- | --- |
| `.venv-base-check/Scripts/python.exe -m pytest -q` | Финальный запуск после retry fix: 1297 passed, 63 skipped, 1162 xfailed, 1 warning; exit 0, 124.26s |
| `.venv-base-check/Scripts/python.exe -m ruff check .` | All checks passed, exit 0 |
| `.venv-base-check/Scripts/python.exe -m ruff format --check .` | 982 files already formatted, exit 0 |
| `.venv-base-check/Scripts/python.exe -m mypy` | 684 files, no issues, exit 0 |
| `.venv-training/Scripts/python.exe -m pytest labs projects/document_intelligence_lab/part_a -q` | 256 passed, 7 skipped, 68 xfailed, 1 warning; exit 0 |
| `.venv-training/Scripts/python.exe -m mypy -p labs -p projects.document_intelligence_lab` | После config-only optional PEFT fix: 122 files, no issues, exit 0 |
| `.venv-tracking/Scripts/python.exe -m mypy -p projects.document_intelligence_lab.tracking_intro` | 5 files, no issues, exit 0 |
| `.venv-rag/Scripts/python.exe -m mypy -p labs.03_real_rag` | 8 files, no issues, exit 0 |
| `.venv-finetuning/Scripts/python.exe -m mypy -p labs.04_llm_finetuning` | 15 files, no issues, exit 0 |

Реальные runtime tests выполнены в opt-in окружениях. Для MLflow ниже указан
завершающий запуск после retry fix; Qdrant/PEFT source после их запуска не менялся:

```powershell
$env:ROADMAP_RUN_MLFLOW = '1'
.venv-tracking/Scripts/python.exe -m pytest projects/document_intelligence_lab/tracking_intro -q
Remove-Item Env:ROADMAP_RUN_MLFLOW
$env:ROADMAP_RUN_QDRANT = '1'
.venv-rag/Scripts/python.exe -m pytest labs/03_real_rag -q
Remove-Item Env:ROADMAP_RUN_QDRANT
$env:ROADMAP_RUN_PEFT = '1'
.venv-finetuning/Scripts/python.exe -m pytest labs/04_llm_finetuning -q
Remove-Item Env:ROADMAP_RUN_PEFT
```

Результаты: MLflow **10 passed / 10.02s**; Qdrant **55 passed, 2 skipped / 9.31s**
(два skip относятся к другим optional model tests); PEFT **28 passed / 21.09s**.
Все exit 0. `uv lock --check` и `git diff --check` также exit 0.
Смысл CLI дополнительно проверен на неизменённом `document-a1-reproduction`:
`scripts/learn.py test document-a1-reproduction` — 12 passed, 2 xfailed, exit 0;
`scripts/learn.py check document-a1-reproduction` — те же tests, **exit 1 / CHECK INCOMPLETE**
из-за двух обязательных student TODO. Это ожидаемый незачёт, не regression failure
и не повод менять реализацию ученика или критерии проверки.
Known full-suite warning: Starlette/AnyIO `BlockingPortal` deprecation, не новая
ошибка упражнений. Не скрыта фильтром. MLflow CLI отдельно предупреждает о trusted
pickle и pip pin; эти предупреждения не означают проверенный production release.
Межокруженческая mypy-проверка выявила отсутствие optional PEFT в training:
исправление конфигурации не добавляет пакет в обязательную группу.

Read-only проверка ссылок, включая untracked материалы: 322 Markdown files,
108 anchors, 0 issues. Локальный Markdown preview проверен в браузере:
таблицы/portable text-схемы registry/PEFT читаемы, actual 24-point `loss.svg`
отображается. Mermaid-only Qdrant заменён переносимой text-схемой; её фактическое
отображение также проверено. GitHub/PyCharm rendering не проверялось.
[CI](continuous-integration.md) добавляет только ручную opt-in matrix, hosted run NOT_RUN.
Независимый review трёх областей и интеграции не нашёл Critical/Important;
три Minor замечания исправлены: retry namespace, portable visual и stale status.
Финальная scoped rereview приняла все три исправления; новых Critical/Important/Minor
не обнаружено. Полный base regression и Ruff/format/mypy повторены после изменения кода.

## Изменения и сохранность

Новые source/material files относительно начала этого продолжения:

- [registry.py](../projects/document_intelligence_lab/tracking_intro/registry.py),
  [registry-lifecycle.md](../projects/document_intelligence_lab/tracking_intro/registry-lifecycle.md),
  [пустой registry report](../projects/document_intelligence_lab/tracking_intro/registry-report-template.md);
- [Qdrant runtime tests](../labs/03_real_rag/test_qdrant_runtime.py),
  [Qdrant verification](../labs/03_real_rag/verification.md);
- [PEFT demo](../labs/04_llm_finetuning/peft_demo.py),
  [PEFT tests](../labs/04_llm_finetuning/test_peft_demo.py);
- этот отчёт.

Дополнены прежние demo/tests/theory/README в тех же labs, dependency groups/lock,
CI и навигация. Новых exercise IDs нет. Не строились platform, UI или новый курс.
Ученические TODO, отчёты, реализации, CLI/catalog/progress и ранние модули не
изменены. Сравнение исходных 1029 non-ignored файлов: 1004 bytes-identical,
25 намеренно дополнены в указанных lab/docs/dependency/CI файлах; 8 новых,
0 удалённых. Все старые student exercise/report/progress/catalog/CLI файлы и
ранние модули bytes-identical. Gitignored outputs/envs/scratch считаются отдельно.
Commit/push/merge не выполнялись; HEAD остаётся
`836028944eceaa260cb47d0056b593af4a4648d4` на `codex/ai-ml-wave1`.

## Что остаётся

**vLLM — DEFERRED_ENV / NOT_RUN:** пользователь 11.10.2026 явно отложил этот пункт,
поскольку на ноутбуке нет Linux/WSL. Установка WSL/Linux не выполняется. В маршруте
сохраняются теория, готовый client и варианты моделей; фактический запуск позднее.
QLoRA, pretrained модели, Docker/cloud и hosted CI также **NOT_RUN**; нужны
отдельные ресурсы и собственные свидетельства исполнения.

## Продолжение R06: предварительная проверка и актуальные gates

Повторная сверка 11.10.2026 после запроса выполнить оставшиеся пункты. Уже
проверенные MLflow/Qdrant/PEFT mechanisms не реализованы повторно. Исправлены
устаревшие общие NOT_RUN в lifecycle README/theory/verification и части B;
в registry guide ссылки ведут на final receipts. NOT_RUN в `integration_demo`
и classification-only lifecycle demo сохранены: эти конкретные flows не
подключают Qdrant/registry. Исторические отчёты не переписаны задним числом.

### Что добавлено

- [Локальная предварительная проверка](../projects/document_intelligence_lab/part_a/preflight.py)
  и [45 новых тестов](../projects/document_intelligence_lab/part_a/test_preflight.py).
- Из существующего `compare` выделена общая `verify_comparison_inputs`:
  три внешних pins → bytes/inventory → methods → data/split/ordered labels.
  Логика не продублирована, прежний inference/evaluation contract сохранён.
- [Инструкция и вариация](../projects/document_intelligence_lab/part_a/README.md#предварительная-проверка-входов--без-обучения),
  текущая карта покрытия и R06-пункт плана уточнены. Новый exercise ID не нужен.

Команда `python -m projects.document_intelligence_lab.part_a.preflight --help`
показывает обязательные локальные пути, три заранее сохранённых SHA-256,
requested seed/device/time/memory budgets. Проверка ничего не пишет, не
загружает pickle/модель, не обучает, не делает inference и не импортирует
Torch/Transformers. Она работает и в base environment без этих packages.
`INPUTS_VERIFIED` **не** подтверждает runnable safetensors, подлинность источника,
обученность, CUDA, фактический бюджет, parity, качество или освоение учеником.

На существующем авторском `artifacts/document-a-teacher-author-001` реально
выполнены команды из README с его ранее сохранёнными pins: корректные inputs
дали `INPUTS_VERIFIED`, execution `NOT_RUN`, quality `NOT_EVALUATED`, exit 0.
Encoder здесь остаётся `teacher-random`. Замена только encoder pin на 64 нуля
дала JSON `BLOCKED_INPUTS`, причина `artifact sha256 differs from saved bytes`,
Python exit 2. Файлы не менялись. Для точной передачи native exit code оболочкой:
`$preflightExit = $LASTEXITCODE; exit $preflightExit`.

### Свежие технические проверки этого продолжения

Из корня существующего проекта, без install/download:

| Команда | Наблюдённый результат |
| --- | --- |
| `.venv-base-check/Scripts/python.exe -m pytest -q` | Финальный после schema fix: 1342 passed, 63 skipped, 1162 xfailed, 1 существующий warning; exit 0, 143.62s |
| `.venv-training/Scripts/python.exe -m pytest labs projects/document_intelligence_lab/part_a -q` | Финальный после schema fix: 301 passed, 7 skipped, 68 xfailed, тот же warning; exit 0, 44.29s |
| `.venv-base-check/Scripts/python.exe -m pytest projects/document_intelligence_lab/part_a -q` | Финальный: 56 passed, 1 optional-training skipped; exit 0 |
| `.venv-training/Scripts/python.exe -m pytest projects/document_intelligence_lab/part_a -q` | Финальный: 57 passed; exit 0 |
| `.venv-base-check/Scripts/python.exe -m ruff check .` | All checks passed, exit 0 |
| `.venv-base-check/Scripts/python.exe -m ruff format --check .` | 984 files already formatted, exit 0 |
| `.venv-base-check/Scripts/python.exe -m mypy` | 686 source files, no issues, exit 0 |
| `.venv-training/Scripts/python.exe -m mypy -p labs -p projects.document_intelligence_lab` | 124 source files, no issues, exit 0 |
| `.venv-base-check/Scripts/python.exe -m pytest tests/integration/test_markdown_links.py tests/tooling/test_documentation.py -q` | 13 passed, exit 0 |
| `uv lock --check` | 241 packages resolved, exit 0; install не выполнялся |

Warning — прежний Starlette/AnyIO `BlockingPortal` deprecation, не скрыт.
Успех этих проверок — техническая приёмка, не ML evaluation и не learner check.
Предыдущие независимые MLflow/Qdrant/PEFT receipts не заменены новым pytest.
Независимое task review обнаружило malformed JSON `evidence_kind=[]/{}`:
изначально это давало TypeError/traceback вместо корректного отказа. Два новых
реальных subprocess regression tests воспроизвели ошибку RED; явная string
schema validation дала GREEN / JSON `BLOCKED_INPUTS`, exit 2. Scoped re-review
подтвердило исправление без новых замечаний. Неожиданные runtime/programmer
ошибки по-прежнему не маскируются общим перехватом TypeError.
Финальное независимое review этого продолжения одобрено: новых
Critical/Important/Minor замечаний нет. Проверены current source, task/fix delta,
документация и записанные post-fix проверки; historical runtime experiments
reviewer повторно не запускал. Это не одобрение всего незавершённого roadmap.
Новая text-схема сверена с input gate и фактическими JSON/exit codes; отдельный
визуальный просмотр Markdown в этой итерации не проводился.
Дополнительная read-only проверка охватила 322 tracked/untracked Markdown files
и 110 local anchors: 0 issues; `git diff --check` exit 0. Mistune AST разбирает
обновлённые part A README и этот отчёт; fences сбалансированы. Это структурная
проверка, не подтверждение отображения в GitHub/PyCharm.

### Открытые этапы до разрешения MiniLM: исторический снимок

| Остаток | Фактическая граница |
| --- | --- |
| R06 pretrained comparison | В проверенных project/default HF cache locations нет pretrained bytes. Есть только random teacher checkpoint. Скачивание backbone само не обучит classifier; student HF runner содержит TODO и не исполняется за ученика |
| R07 semantic retrieval + generator | Local Qdrant mechanics уже проверены; нужен явно разрешённый encoder snapshot и отдельно выбранный generator. Ручные vectors/excerpt callable не переименовываются в embeddings/LLM |
| R09 полный lifecycle | Совместный data/model/preprocessing/corpus/representation/index release, shadow/canary и real drift evidence остаются открыты; текущий classification release явно имеет `index=null` |
| R11 pretrained LoRA/QLoRA | Actual random-LM PEFT опыт готов; pretrained comparison и CUDA/QLoRA не выполнены |
| Docker/PostgreSQL | `Get-Command docker` и `Get-Command psql` дали NOT_FOUND. Это проверка наличия CLI, не доказательство отсутствия любого удалённого сервера. Установки/поиск доступов не выполнялись |
| RTX 5060 | `nvidia-smi`: RTX 5060 Laptop, 8151 MiB, driver 616.64. В `.venv-training` Torch 2.14.0+cpu, `torch.version.cuda=None`, `cuda.is_available()=False`; GPU experiment NOT_RUN |
| Cloud и hosted CI | Не выбраны provider/region/budget/access; публикация/запуск GitHub workflow без разрешения не выполняются |
| vLLM | DEFERRED_ENV по вашему решению; Linux/WSL не устанавливаются |
| Самостоятельный capstone | Реализации, отчёты, выводы и защита остаются работой ученика, REQUIRES_REVIEW |

Ближайший model gate — уже закреплённый `sentence-transformers/all-MiniLM-L6-v2`,
revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`: шесть разрешённых файлов,
91 567 205 bytes (~92 MB), по существующему `resources.json`. До явного разрешения
они не скачиваются. Для R07 датасет Bitext не нужен: переиспользуется neutral
author corpus. Существующий downloader по умолчанию получает **и model, и dataset**;
не запускайте его вслепую, если согласована только модель.

Работа продолжена в существующей dirty branch, чтобы не потерять накопленные
материалы; scratch сохранён, поскольку Git snapshot не создаётся. Это сознательное
ограничение: нужна аккуратная локальная сверка пересечений, не замена истории.
Student TODO/report/progress/CLI/catalog/IDs, зависимости и lock не изменены.
SHA-256 сверка исходных 1037 non-ignored файлов: 1027 побайтно сохранены,
10 намеренно дополнены (part A protocol/README и status/navigation docs),
2 новых preflight files, 0 удалений. Исходные student code/reports/progress,
CLI/catalog и dependency files побайтно неизменны.
Commit/push/merge не выполнялись. Все недоступные или самостоятельные этапы
остаются открытыми, а не отмечены выполненными.

<a id="r07-r09-local"></a>

## R07 MiniLM → локальный R09: явный model run и совместное восстановление

11.10.2026 пользователь разрешил скачать **только MiniLM (~92 MB)** и выполнить
R07, затем локальный R09. Получены шесть pinned files, total91 567 205 bytes;
size/SHA-256 и exact inventory проверены существующими `fetch_verified` /
`verified_minilm_identity`. Bitext отсутствует, других моделей/датасетов не
скачивали. Generator согласуется отдельно; vLLM остаётся DEFERRED_ENV.

### R07: что действительно измерено

Из корня фактически выполнено, exit0:

```powershell
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
.venv-training/Scripts/python.exe -m labs.03_real_rag.dense encode-local --model-dir .cache/roadmap-huggingface/model --output artifacts/r07-minilm-cls-20261011-v1
```

Torch2.14.0+cpu/Transformers5.17.0/NumPy2.5.3, eval/inference, batch≤8,
max_length128, dimension384, **CLS + L2**, не рекомендованный mean pooling.
Существующие corpus/judgments не переписывались. [Per-query таблица и digests](../labs/03_real_rag/verification.md#minilm-local):
на трёх answerable teacher queries mean Recall@2/MRR lexical2/3, CLS1;
на двух zero-positive queries metricsnull. Dense всё равно возвращает public
соседей на absent/protected вопросах: это не доказательство answerability.
Порог по пяти случаям не подбирался, общего semantic качества не заявляем.

Дополнительный query-vector run записал seed17, версии, PID/time, полную embedding
identity и исходные judgments; external record SHA
`2cf5f89e81d95174fc5e1130943f0ff136a489c9a54cf10b8db738615690db87`.
В `.venv-rag` численные vectors загружены в новый local `r07_pristine` Qdrant:
**все пять actual public query top2 совпали с NumPy IDs/scores** (atol/rtol1e-6).
Новый process сверил все четыре point IDs/payload/vectors, dimension/cosine,
metadata и повторил выдачу. `artifacts/r07-minilm-pristine-qdrant-20261011-v1/`
содержит `retrieval-receipt.json` и `fresh-process-receipt.json` (PID30112/9896).
Это actual retrieval evaluation на tiny author cases, не LLM evaluation.

Старый `qdrant-smoke` также прошёл с real MiniLM vectors, но его изменённый text
переиспользует прежний vector. Этот index **mechanisms-only**, не корректный
semantic release. Поэтому для B отдельно заново encoded изменённый HOURS@2
(16:00→15:00), SCAN revoked, APPENDIX удалён. Old/new HOURS cosine0.9908628759,
vectors различны; прежние relevance labels HOURS@1 не применялись к B.
CPU выбран намеренно: маленькому encoder не требуется занимать RTX5060 VRAM;
CUDA/GPU experiment не проводился. Memory/стоимость NOT_MEASURED, не выдуманы.

### R09: новые файлы и сохранённые контракты

- [Coupled local release](../labs/06_ml_lifecycle/coupled.py): совместно выбирает
  две teaching branches, не приравнивает classification dataset к RAG corpus.
- [Offline tests](../labs/06_ml_lifecycle/test_coupled.py) и
  [явно gated Qdrant tests](../labs/06_ml_lifecycle/test_coupled_runtime.py).
- [Русский разбор, схема и команды](../labs/06_ml_lifecycle/coupled-recovery.md).

Старые `releases.py` schema1/`index=null` и `dense.py` contracts не менялись.
Новый `coupled-release.json` копирует verified classifier release, corpus/chunks/
vectors snapshot и все шесть encoder files. Внешний pin связывает model/data/split/
preprocessing обеих веток, representation и logical index contract. Base verify
не импортирует Torch/Transformers/Qdrant и не десериализует pickle. Restore
classifier переиспользует actual ASGI readiness/inference; pickle trust явно
отделён от SHA. `.venv-rag` отдельно строит **новый** local index из pinned vectors.
Обычный pytest/sync/download default не изменён. Новых dependencies/IDs нет.

### Фактические commands и A→B→A

Текущие artifacts — **v2**, пересозданные в новых папках после code review:
storage проверяется рекурсивно до открытия Qdrant, включая collection и SQLite/lock
paths. Два реальных Windows junction regression cases прошли RED→GREEN; scoped
re-review подтвердил исправление. v1 сохранены как история, не перезаписаны.
Source identity входит в manifest, поэтому новые outer pins ниже отличаются от v1.

Пример реально выполненного write A; повторять только с новыми output/receipt:

```powershell
.venv-base-check/Scripts/python.exe -m labs.06_ml_lifecycle.coupled write --classification-release artifacts/r09-author-lifecycle-v1/release-A --classification-release-sha256 28657dae46abd5baa95916fbb4aa8e454b8ee3406dad81a96d35ee6d5df83df8 --snapshot artifacts/r07-minilm-cls-20261011-v1 --snapshot-sha256 25c7d66fbe0cc42aef6badf7e2782211c3e82485ce7a18f0ef1acfaf2a10e374 --model-dir .cache/roadmap-huggingface/model --output artifacts/r09-coupled-A-20261011-v2 --receipt artifacts/r09-coupled-receipts-20261011-v2/write-A.json
```

Зафиксированные снаружи outer pins:
A `2366d8ffcf02d0aeb8c44104f02bad2c3d0d5108a35606da260291c210ade72b`;
B `a02c0173adde267a0e9212548a7b82d8060407fa15f4024f007779521179f373`.
B write использовал ранее pinned classification B
`b89d39261fa4990fe6a0404c10793ccdee219a5ccdfbf9df2383d7b1627175f7`
и re-embedded snapshot `9debc56f4b41b4a14629b49269025b0cd0275400a55fedf9f0e04cb5bd3e38a4`.
Оба release содержат собственные model bytes и не зависят от оригинального cache.

Фактический rollback после восстановления B, три отдельных процесса, exit0:

```powershell
.venv-base-check/Scripts/python.exe -m labs.06_ml_lifecycle.coupled restore --root artifacts/r09-coupled-A-20261011-v2 --release-sha256 2366d8ffcf02d0aeb8c44104f02bad2c3d0d5108a35606da260291c210ade72b --output artifacts/r09-coupled-rollback-A-20261011-v2 --receipt artifacts/r09-coupled-receipts-20261011-v2/rollback-A.json
.venv-rag/Scripts/python.exe -m labs.06_ml_lifecycle.coupled index --root artifacts/r09-coupled-rollback-A-20261011-v2 --release-sha256 2366d8ffcf02d0aeb8c44104f02bad2c3d0d5108a35606da260291c210ade72b --storage artifacts/r09-coupled-index-rollback-A-20261011-v2 --receipt artifacts/r09-coupled-receipts-20261011-v2/index-rollback-A.json
.venv-rag/Scripts/python.exe -m labs.06_ml_lifecycle.coupled verify-index --root artifacts/r09-coupled-rollback-A-20261011-v2 --release-sha256 2366d8ffcf02d0aeb8c44104f02bad2c3d0d5108a35606da260291c210ade72b --storage artifacts/r09-coupled-index-rollback-A-20261011-v2 --receipt artifacts/r09-coupled-receipts-20261011-v2/fresh-process-A.json
```

| Явно выбранная версия | ASGI `triangle` → label | Qdrant points / public | Наблюдение |
| --- | --- | --- | --- |
| A | circle | 4 / 3 | HOURS@1 16:00, SCAN public |
| B | triangle | 3 / 1 | HOURS@2 15:00, SCAN staff, APPENDIX отсутствует |
| Wrong external pin | не запускался | не создавался | Python exit1; output/receipt не появились |
| NEW rollback A | circle | 4 / 3 | Точный исходный inventory и пять original query rankings восстановлены |

```text
classification A + corpus A + exact MiniLM + index config
                 → NEW classifier A + NEW index A
classification B + re-embedded corpus B + same representation
                 → NEW classifier B + NEW index B
explicit old A pin → NEW classifier A + NEW index A → fresh process verify
```

Receipts в `artifacts/r09-coupled-receipts-20261011-v2/` содержат каждый PID,
UTC/версии/pins/time. После rollback ASGI PID21020 ready, index PID16808,
fresh verifier PID29988: все четыре exact points/payload/vectors/metadata.
Inventory SHA `595027b7cb583bf0e7cf279e3cc10b853af6ab59ae151d37c319a363997ca262`
совпадает с A. Дополнительный process PID11372 повторил пять real question vectors
для A/B/rollbackA и сравнил classifier probe/inventory/rankings A с восстановленным A.
`sequence.json` SHA `cb5d72247b129e18e833a65add638395ecec55f96af9eb808a8c21b717ca3d5e`.
B queries показывают актуальный HOURS@2; quality по прежним labels не считалась.
Registry MLflow из прежнего опыта не дублировался и не был автоматически promoted.

Первый дополнительный aggregate check остановился на точном равенстве floating
scores: повторная нормализация query дала delta −1.11e-16 при тех же IDs. Read-only
проверка установила причину; финальный aggregate использует заявленный
`atol=rtol=1e-6` для чисел, точное равенство для IDs/payload/file pins. Recovery и
index не перезаписывались. Это operator-check correction, не изменение ML results.

### Границы и решения

1. Новый отдельный format сохраняет прежний classification schema1 и student contracts;
   цена этого решения — поддержка ещё одного малого local format.
2. Qdrant восстанавливается из logical snapshot, не копированием server DB backup;
   server/crash/atomic deployment recovery потребует отдельного опыта.

Verify требует matching code hashes и Python3.12.14/NumPy2.5.3; это строгий local
protocol, не автоматическая миграция runtime. Partial failure retains новую папку
для inspection, повтор не перезаписывает её. Новые receipts хранятся **вне** pinned
artifact trees; output/index нельзя вкладывать в исходный release. Links/junctions
и их ancestors отвергаются. SHA подтверждает bytes, не происхождение vectors,
подлинность издателя или безопасность pickle. Actual encoder evidence отдельное.

Historical ACL A при rollback снова содержит public SCAN только в privileged
synthetic parity check. **Нельзя откатывать текущую authorization policy вместе
с моделью:** перед serving нужны authoritative current ACL/source recheck и
отдельное сохранение revoke tombstones. Этот helper live authorization не реализует.

Не выполнены: generator/answer-quality, vLLM/Linux/CUDA, coupled MLflow alias
promotion, server ANN/concurrency/crash/atomic switch, shadow/canary, production
drift/labels, Docker/cloud/hosted CI. Student implementations/reports/защита остаются
REQUIRES_REVIEW. Этот локальный пакет не закрывает весь production R09 или часть B.

### Проверки после исправления, 11.10.2026

Все команды ниже выполнены из корня; успешные invocation exit0:

| Команда | Фактический результат |
| --- | --- |
| `.venv-base-check/Scripts/python.exe -m pytest -q` | 1378 passed, 78 skipped, 1162 xfailed; 148.09 s |
| `.venv-training/Scripts/python.exe -m pytest labs projects/document_intelligence_lab/part_a -q` | 337 passed, 22 skipped, 68 xfailed; 62.49 s |
| `$env:ROADMAP_RUN_QDRANT='1'`, затем `.venv-rag/Scripts/python.exe -m pytest labs/03_real_rag labs/06_ml_lifecycle -q` | 115 passed, 6 skipped; 36.63 s |
| `.venv-base-check/Scripts/python.exe -m ruff check .` | All checks passed |
| `.venv-base-check/Scripts/python.exe -m ruff format --check .` | 988 files already formatted |
| `.venv-base-check/Scripts/python.exe -m mypy` | no issues, 686 source files |
| `.venv-training/Scripts/python.exe -m mypy -p labs -p projects.document_intelligence_lab` | no issues, 127 source files |
| `.venv-base-check/Scripts/python.exe -m mypy -p labs.06_ml_lifecycle` | no issues, 9 source files |
| `uv lock --check` | 241 packages resolved, lock unchanged |
| `uv pip check --python .venv-base-check/Scripts/python.exe` | 156 packages compatible |
| `uv pip check --python .venv-training/Scripts/python.exe` | 193 packages compatible |
| `uv pip check --python .venv-rag/Scripts/python.exe` | 163 packages compatible |
| `git diff --check` | no whitespace errors |

Есть один прежний upstream Starlette/AnyIO `BlockingPortal` deprecation warning.
Runtime tests по умолчанию gated: это не student credit. В explicitly gated rag
scope два optional Torch tests, три file-symlink cases без Windows privileges и
один non-Windows FIFO case пропущены; реальные collection/nested junction cases
прошли. Ученические xfail сохранены, строгий `check` не ослаблялся.

Одна неверная диагностическая invocation `mypy .` отказалась от numeric package
имени; затем выполнены штатные configured `mypy` и package-based commands выше.
Установки/sync здесь не повторялись: использованы уже существующие три окружения,
проверены их зависимости. Изменений dependency groups/lock нет.

Сверка SHA256 исходных 1039 nonignored files: 1027 побайтно прежние, 12 намеренных
documentation updates, 4 новых файла, 0 удалено. Все student implementations/TODO/
report templates/progress, CLI/catalog/IDs, старые runtime helpers и dependency
files сохранены. HEAD `836028944eceaa260cb47d0056b593af4a4648d4`, ветка
`codex/ai-ml-wave1` не менялись; commit/push/merge не выполнялись.

Документация и отображение: `.venv-base-check/Scripts/python.exe -m pytest
tests/integration/test_markdown_links.py tests/integration/test_packet6_rag.py
tests/integration/test_packet7_production.py -q` — **25 passed**, 5.10 s
(повторено после последней wording correction).
Дополнительный read-only script применил existing link checker ко всем tracked и
untracked nonignored Markdown и сверил heading/explicit anchors: **323 файла,
121 anchors, 0 issues**. Временный loopback Mistune preview в браузере визуально
проверен: таблица пяти R07 queries, схема release, таблица A→B→A и русский текст
читаемы, без перекрытий. Это не проверка GitHub renderer: preview экранирует raw
HTML anchors; их существование проверено отдельно. Preview не является новым
приложением проекта и не нужен для обучения. Понимание учеником не проверялось.

Финальное независимое ревью: Critical0 / Important0 / Minor1. Проверены все 16
scoped file hashes, actual code/sequence/A/B pins и соответствие receipts отчёту.
Minor — устаревшее общее NOT_RUN в RAG theory — исправлен уточнением области
исторического hand-vector опыта и ссылкой на MiniLM measurement. Код после full
regression не менялся. Генератор и полный production lifecycle в этот зачёт не входят.
