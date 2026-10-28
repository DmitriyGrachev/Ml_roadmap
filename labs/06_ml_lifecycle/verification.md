# R09: author evidence и открытые gates

Дата: 2026-10-11. Авторский bounded scope выполнен на существующем Windows CPU
base окружении, без installs/downloads/model resources/servers/cloud/Git mutations.
Ниже сохранён протокол первоначального classification-only опыта. Позднее
[local MLflow runs/registry/replay](../../docs/local-runtime-continuation.md)
проверены отдельно. Позднее локальный согласованный model/preprocessing/corpus/index
release [проверен ниже](#coupled-local); production deployment остаётся **NOT_RUN**.
Ученик — **REQUIRES_REVIEW**. Старые learner
code/TODO/IDs/progress сохранены.

## Реально выполнено

```powershell
.venv/Scripts/python.exe -m labs.06_ml_lifecycle.demo --output artifacts/r09-author-lifecycle-v1
.venv/Scripts/python.exe -m pytest labs/06_ml_lifecycle -q
.venv/Scripts/python.exe -m ruff check labs/06_ml_lifecycle
.venv/Scripts/python.exe -m ruff format --check labs/06_ml_lifecycle
.venv/Scripts/python.exe -m mypy --follow-imports=silent -p labs.06_ml_lifecycle
```

Результат: demo exit 0; **13 passed**, одна upstream Starlette
`anyio.abc.BlockingPortal` deprecation; Ruff/format passed; mypy success на
6 source files в последнем scope invocation. Numeric package требует `-p`:
проверка самого пути с `__init__.py` не умеет выводить имя `06_ml_lifecycle`.
Полный regression запускает parent при интеграции; этот документ не утверждает
успех полной suite по отдельным локальным checks.

Python 3.12.14, FastAPI 0.141.1, Starlette 1.6.0, scikit-learn 1.9.1.
ASGI in-process TestClient, CPU. R04 `run_recovery` переиспользован, не продублирован.
Source measurement хранится в ignored `artifacts/r09-author-lifecycle-v1/`:

| Stage | Actual startup seconds | Actual probe |
| --- | ---: | --- |
| A | 0.08149189967662096 | circle |
| B | 0.011912300251424313 | triangle |
| wrong digest | 0.005471499636769295 | startup rejected |
| fresh A | 0.00821880018338561 | circle |

6 warm-after-startup ASGI requests, status 200. Median 0.0018575000576674938 s,
observed maximum 0.002650500275194645 s. Это не оценка p99/throughput/load.

Release A external digest:
`28657dae46abd5baa95916fbb4aa8e454b8ee3406dad81a96d35ee6d5df83df8`.
Release B external digest:
`b89d39261fa4990fe6a0404c10793ccdee219a5ccdfbf9df2383d7b1627175f7`.
A bundle digest:
`8e7243a10a29b0f02f3d354e8ff092feae55b391e0c9de995e06b39057f437da`.
Digest этой completed release не хранится внутри неё: оператор фиксирует его
в отдельном record. Release copies включают verified bundle inventory.

`recovered-A/restart.json` подтверждает actual fresh lifespan/readiness,
`triangle → circle`, preprocessing version 1 и exact A bundle identity.
Ещё один отдельный Python process вызвал `restore_release_new` с **literal fixed
release digest выше**, а не пересчитанным expected. Новый каталог
`artifacts/r09-author-lifecycle-fresh-process-v1` получил те же identity и ответ.
Это fresh-process ASGI restart smoke, не TCP/deployment proof.

Все четыре constructed windows имеют n=4, label support 4/4, 4/4, 4/4, 0/4.
Actual model accuracy: 1.0, 0.5, 0.0, null. Triangle fractions: 0, 0.5, 0, 0.5.
Warm CPU direct-call median в ms: 0.003700144588947296, 0.0032498501241207123,
0.003050081431865692, 0.0030498486012220383. Это 16 tiny actual calls на authored
inputs/labels, не live traffic/quality. Validation inference до измерения и loader
replay делают все измеренные calls warm. Memory null с причиной: native/process
peak не instrumented; timing не оценивает memory.

SVG содержит title/description, samplecounts/label support, separate fraction/
accuracy и ms scales; XML parsing и chart generation passed. Первоначальный browser
file preview был запрещён URL policy (только http/https), author обход не предпринимал.
Затем controller проверил actual generated SVG через свой уже запущенный временный
loopback QA server: full-page screenshot читаем, без overlaps; четыре n=4 windows,
quality [1,.5,0,unknown], feature [0,.5,0,.5], delayed labels 0/4 соответствуют raw
report. Это controller visual evidence конкретного artifact, не lifecycle API/server
или production deployment proof. R04 timeline также визуально проверен controller.

## Что покрывают tests

Actual copied release/recovery/restart, relocated bundle, fixed external digest,
identity tamper даже с пересчитанным release digest, missing model fail до создания
destination, no overwrite, partial-label denominator, absent-label unknown,
changed target relation при прежних inputs, malformed label evidence,
actual demo/quality/time/SVG и offline external/TCP guard.

Tests были добавлены перед implementation: начальный RED — отсутствующий feature
module при collection, затем implementation. Первый run дал 9 passed/3 failed:
глобальный labs offline guard блокировал Windows asyncio loopback socketpair.
По указанию parent глобальный guard сохранён, в scoped tests разрешён только
numeric loopback для event loop; HTTPX TCP transports отдельно запрещены.
Финальный focused run — 13 passed. Ни fake tracker, ни mocked inference не использованы.

## Что остаётся отдельным gate

- MLflow actual local runs/storage/flavors/registry/alias/replay теперь проверены
  в [отдельном опыте](../../projects/document_intelligence_lab/tracking_intro/registry-lifecycle.md);
  [текущий runtime-протокол](../../docs/local-runtime-continuation.md) содержит
  версии, команды и ограничения. Этот classification-only demo registry не вызывает.
  Совместное promotion service/index release остаётся NOT_RUN; JSON release file
  сам по себе не считается Model Registry.
- RAG corpus/index/embedding rollback не входит в старый classification-only demo,
  `index=null`; он не принимает и не имитирует retrieval bundle. Новый отдельный
  coupled local опыт описан ниже, а не приписан старому runner.
- Memory-aware preparation/backfill здесь объяснены через готовые stream/data
  release contracts; новый teacher не решает их learner implementation и не
  доказывает memory bound/pipeline completion. Нужны самостоятельные replay/measurements.
- Shadow/canary, Docker/TCP, hosted CI/cloud, real drift monitoring, labels из
  production и pretrained/generalization quality — NOT_RUN.
- Human decisions, independent learner incident/transfer/defense — REQUIRES_REVIEW;
  пустой report и author tests не создают student completion.

Теория следует existing lesson template: prerequisites, прогнозы, механизм/схемы,
worked actual example, altered digest line, failure/limits, семь вопросов,
независимый перенос и ограниченные источники. TDD и fresh verification применены
к code/tests; computer/browser preview попытка завершилась policy rejection.

<a id="coupled-local"></a>

## Дополнение: реальные MiniLM releases A→B→A

Новый [coupled.py](coupled.py), [offline tests](test_coupled.py),
[gated disk tests](test_coupled_runtime.py) и [русский runbook](coupled-recovery.md)
переиспользуют старые classification/snapshot verifiers. Схема старого release,
CLI/course ID/student TODO/progress не менялись. Новых зависимостей нет.

После разрешённого скачивания только MiniLM выполнен реальный local опыт:
Текущие данные ниже — повторный v2 после recursive storage path preflight fix;
v1 retained historical. Collection/SQLite/lock descendant links запрещены до
client open, два настоящих Windows junction cases проверены RED→GREEN.
`artifacts/r09-coupled-receipts-20261011-v2/sequence.json`,
SHA `cb5d72247b129e18e833a65add638395ecec55f96af9eb808a8c21b717ca3d5e`, PID11372.
Полные команды, runtime и проверки — [текущий отчёт](../../docs/local-runtime-continuation.md#r07-r09-local).

| Явный выбор оператора | Classifier probe `triangle` | Index snapshot | Результат |
| --- | --- | --- | --- |
| A | circle | 4 chunks, SCAN public, HOURS@1 16:00 | ASGI ready; exact local index |
| B | triangle | 3 chunks, SCAN staff, HOURS@2 15:00, APPENDIX удалён | Новый HOURS реально re-embedded; один public chunk |
| Wrong external pin | не запускался | не создавался | Python exit1; output/receipt отсутствуют |
| Возврат A в NEW storage | circle | те же 4 original chunks | Classifier, полный inventory и пять query rankings совпали с A |

A outer pin: `2366d8ffcf02d0aeb8c44104f02bad2c3d0d5108a35606da260291c210ade72b`.
B outer pin: `a02c0173adde267a0e9212548a7b82d8060407fa15f4024f007779521179f373`.
Code SHA: `9674f1243050cc878b9e280dfc880e423692ef6ab65360e12deb924a080bfa24`.
После rollback новый process PID29988 независимо открыл уже закрытый Qdrant:
inventory SHA `595027b7cb583bf0e7cf279e3cc10b853af6ab59ae151d37c319a363997ca262`,
четыре points, exact payload/vectors/metadata, public top1 SCAN. Это self-query parity,
не ML evaluation. Отдельный PID11372 проверил пять actual question vectors:
A и rollback A идентичны; B выдаёт только HOURS@2. Старые judgments для B не считались.

Скопированы все model bytes, не только путь к cache; восстановление не требует
исходных папок, обучения, сети или generator. Verify требует тот же code и точные
Python3.12.14/NumPy2.5.3; другой runtime/source отклоняется. Это ограничение данного
локального протокола, не обещание автоматической миграции окружения.

Исторический ACL A в этом privileged synthetic опыте снова содержит public SCAN.
**Это не разрешение отменить текущий revoke:** для serving надо отдельно сохранить
актуальную authorization policy/tombstones и перепроверить current source/ACL.
Helpers не реализуют этот live слой и не публикуют ответы пользователям.

Не проверены: coupled release promotion через MLflow alias, server binary backup,
crash/atomic switch, canary/shadow, реальные drift/labels, hosted CI/deployment.
Generator null/NOT_RUN; vLLM DEFERRED_ENV. Author evidence не заполняет student report.
