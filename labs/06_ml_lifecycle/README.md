# Tracking, deployment и model lifecycle

CORE на уровне одного сервиса. Авторские материалы и CPU smoke READY.
Настоящие local MLflow runs/storage/flavors, registry 1→2→1 и fresh-process replay
проверены [отдельным опытом](../../docs/local-runtime-continuation.md).
Локальный согласованный classification + preprocessing + MiniLM corpus/index
release и восстановление A→B→A теперь **PASS**: [разбор и команды](coupled-recovery.md).
Это две совместно выбранные teacher branches, не одна обученная RAG-модель.
Container/cloud, production promotion и реальные эксплуатационные данные —
**NOT_RUN**. Освоение — **REQUIRES_REVIEW**.
Предупреждение drift само по себе не разрешает retraining или promotion.

Prerequisites: [две модельные labs](../../docs/roadmap.md),
[serving](../05_model_serving/README.md),
[module 08](../../modules/08_production_ai/README.md),
[data-release-study](../../modules/03_data_foundations/exercises/data_release/README.md),
[Document A1](../../projects/document_intelligence_lab/part_a1/README.md),
[CPU service/recovery](../../projects/document_intelligence_lab/service/README.md)
и [tracking introduction](../../projects/document_intelligence_lab/tracking_intro/README.md).

Читайте [теорию](theory.md), затем [локальный runbook](runbooks/recovery.md)
и [recipe полного release promotion](runbooks/registry.md). Он отличает уже
проверенный локальный registry от ещё не выполненного полного lifecycle. Самостоятельная
[вариация](exercise/README.md) отличается от teacher сценария; её
[report](exercise/report-template.md) пуст. Здесь нет нового exercise ID:
проверки автора не дают ученику автоматический зачёт старых заданий.

Из корня, существующий base interpreter; команды ничего не устанавливают:

```powershell
.venv/Scripts/python.exe -m labs.06_ml_lifecycle.demo --output artifacts/MY_NEW_LIFECYCLE
.venv/Scripts/python.exe -m pytest labs/06_ml_lifecycle -q
.venv/Scripts/python.exe -m ruff check labs/06_ml_lifecycle
.venv/Scripts/python.exe -m ruff format --check labs/06_ml_lifecycle
.venv/Scripts/python.exe -m mypy --follow-imports=silent -p labs.06_ml_lifecycle
```

`--output` должен быть новым. Tests используют временные каталоги и запрещают
внешний network/TCP HTTP. Windows event loop требует внутренний numeric loopback
socketpair; он разрешён только в scoped tests, это не запуск API по TCP.
Demo использует настоящий in-process ASGI TestClient; сервер не стартует.

Demo переиспользует `service.recovery.run_recovery`: реальный A rules → B fitted
TF-IDF → rejected digest → fresh A. Затем сохраняет полные copies `release-A/B`,
восстанавливает A в **новый** `recovered-A` и проверяет readiness/inference.
`release.json` связывает actual bundle bytes с data/split/sources, model,
preprocessing, config, code и версиями. Его digest фиксируется **снаружи**;
доверие издателю и безопасность pickle из совпадения SHA-256 не следуют.
Старый classification-only flow имеет `index=null` и сохранён без изменения.
Новый отдельный [coupled release](coupled.py) копирует этот release, exact MiniLM
bytes и согласованный corpus/vector snapshot. Внешний digest фиксирует их совместный
выбор, а не равенство classification dataset и RAG corpus. Base восстанавливает
реальный ASGI classifier; отдельная `.venv-rag` заново строит и проверяет local
Qdrant. [Наблюдённые A/B/rollback результаты](verification.md#coupled-local)
не являются live deployment, atomic switch или разрешением вернуть старые права:
перед serving нужны текущие authoritative ACL/source checks.

`lifecycle.json` содержит real CPU timings и predictions на явно constructed
windows; `monitoring.svg` показывает feature fraction, качество только по
доступным labels и warm median. Это не промышленный drift detector, не p99,
не measurement памяти и не доказательство generalization. `service-recovery/`
содержит исходные ASGI timings и diagram из R04.

Expected full lab artifacts: memory-aware повторяемый data release без дублей,
annotation/schema/provenance, snapshot/split, реальные MLflow runs/artifacts/registry,
human promotion policy, shadow/canary, CI/deployment smoke, совместимый rollback,
observability, incident review. [Author scope и открытые gates](verification.md).
Платное облако необязательно; object storage, identities/permissions, secrets,
network, logs/budget/cleanup требуют собственной явной среды. Kubernetes,
Terraform, Spark и Airflow остаются OPTIONAL.
