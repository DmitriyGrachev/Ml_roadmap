# Local registry: promotion, rollback и независимый replay

Продолжение R04/R09 после [tracking intro](README.md), на тех же A1 bundles.
Цель: восстановить точную выбранную версию после смены alias и после завершения
процесса. MLflow 3.17.0, SQLite и local files; server/UI, hosted registry,
container/cloud и автоматическое решение о качестве не запускаются.

## Что именно меняется

Run хранит условия эксперимента, metrics и связи. Storage хранит bytes: SQLite
не содержит fitted pipeline вместо artifact directory. Flavor задаёт способ
загрузки и input contract. Registry объединяет версии и хранит mutable alias.
Release — решение оператора, связывающее выбранные version/run/digests, runtime,
preprocessing и проверку inference; перенос alias сам по себе не разворачивает service.

```text
A1 fitted pipeline → run + full bundle → logged sklearn flavor
                          │                       │
                          │                registry version 1 / 2
                          │                       │
                          │                champion: 1 → 2 → 1
                          │                       │
                          └─ manifest pin ← operator release pins
                                      │
                              NEW bundle restore
                                      │
                     raw texts → preprocessing → actual predictions
```

Registry source и run artifact URI перед чтением проверяются на `file:` и
containment выбранного root; remote URI отвергается. Отдельный SHA-256 flavor
inventory связывает относительные имена и hashes всех его файлов, включая
`MLmodel` и `model.pkl`. Bundle manifest pin проверяет исходные A1 bytes, data,
splits, config, code, package versions и test predictions общим loader.
Затем загружается настоящий flavor и его predictions сравниваются с bundle.

Это trusted local pickle. Храните SQLite, artifacts и operator config в каталоге,
куда не пишут посторонние процессы; directory links не поддерживаются. Hash
проверяет сохранность, а доверие задаёт оператор. Проверки не защищают от
concurrent replacement между проверкой и чтением. Alias разрешается в version
один раз; inference использует проверенный source этой version.

## Разобранный пример по шагам

Сначала предскажите: если seed 17 и 29 дают одинаковые labels, как доказать
rollback? Совпадения score и labels недостаточно: надо вернуть version/run,
bundle/model/flavor digests и заново выполнить inference из восстановленных bytes.

В author smoke обучаются два TF-IDF/LogisticRegression pipeline на одном cohort.
Это демонстрация lifecycle, а не доказательство превосходства seed 29.

1. `demo` создаёт два fitted A1 runs и сохраняет реальные run IDs в `tracking.json`.
   Их six-row test даёт `accuracy=1`, `macro_f1=1`; одинаковые predictions допустимы.
2. `registry` создаёт новый registered model и версии 1 и 2 из local flavor bytes.
   У каждой версии закреплены run ID, bundle digest и flavor digest.
3. До каждого движения alias preflight восстанавливает bundle в новый каталог,
   проверяет pins и actual flavor predictions. Потом оператор явно выполняет
   `set_registered_model_alias(..., "champion", version)` и перечитывает SQLite.
4. Последовательность `initial=1`, `promotion=2`, `rollback=1` записывается в
   `registry.json`. Rollback вновь загружает bytes версии 1, а не меняет только label.
5. Отдельная команда в новом Python process читает сохранённые operator pins,
   разрешает persisted alias, повторяет bundle restore и flavor inference.
   `restart-verification.json` появляется только после успешного replay.

```powershell
.venv-tracking/Scripts/python.exe -m projects.document_intelligence_lab.tracking_intro.demo --output artifacts/r04-tracking-new
.venv-tracking/Scripts/python.exe -m projects.document_intelligence_lab.tracking_intro.registry --tracking artifacts/r04-tracking-new --output artifacts/r09-registry-new
.venv-tracking/Scripts/python.exe -m projects.document_intelligence_lab.tracking_intro.registry --selected-config artifacts/r09-registry-new/registry.json --output artifacts/r09-restart-new
```

Каждый output должен отсутствовать. Последняя команда — отдельный process,
а не продолжение in-memory run. `--selected-config` принимает только выбранный
оператором protected local report, никогда пользовательский HTTP payload.
Новый lifecycle на том же tracking input получает отдельное registered-model name
с UUID suffix; имя сохраняется в operator pins `registry.json`. Поэтому повтор
в новом output, в том числе после частичного сбоя, не переиспользует и не удаляет
версии или aliases предыдущего lifecycle. Незавершённые записи остаются в registry;
это не транзакционный cleanup или crash recovery.
Несовпадение alias version, run/bundle identity, flavor hash, local URI или
predictions останавливает replay; оно не исправляется записью успешного статуса.
CLI не устанавливает environments. `_mlflow()` выключает telemetry до import.

Author runtime evidence: `artifacts/runtime-continuation-r04-v2/tracking.json`,
`artifacts/runtime-continuation-r09-final/registry.json` и
`artifacts/runtime-continuation-r09-final-restart/restart-verification.json`.
Исторические receipts до окончательного source/retry fix сохранены, но не
заменяют [финальный протокол](../../../docs/local-runtime-continuation.md).
IDs/digests берите из этих файлов, они не константы курса. Saved metrics относятся
только к authored shapes, memory usage остаётся unknown в A1 measurement.
`quality_defense=REQUIRES_REVIEW`, `hosted_deployment=NOT_RUN`.

## Независимая ручная вариация

Возьмите два собственных fitted sklearn bundles с одинаковыми frozen splits,
свяжите их с run IDs через `track_bundle`, затем выберите их local tracking output
для registry. Если используете другой метод/model format, явно объясните границу
этого примера: rules JSON сюда не подходит. Не меняйте teacher/test cohort ради score.
Запишите собственную причину promotion: здесь seed change не аргумент качества.

В новом output выполните rollback и restart. Сравните model и flavor hashes
с предыдущей выбранной version. Затем отдельно поменяйте ожидаемую version в
копии operator config: replay должен отказать до загрузки. Повторите с неверным
flavor hash. Не редактируйте исходный completed bundle или преподавательские reports.
Заполните пустой [собственный отчёт](registry-report-template.md).

Проверьте себя: почему alias может измениться без изменения model bytes? Почему
registry version и logged-model ID различны? Что потеряно при удалении artifact
directory? Почему одинаковые predictions не доказывают rollback? Что должен
проверить service до принятия raw texts? Где сохранено решение оператора о release?

Проверка: gated `test_optional_round_trip.py` использует настоящий SQLite MLflow,
запрещает socket connections и проверяет 1→2→1, pins и predictions, а также два
независимых lifecycle на одном tracking input с replay обоих сохранённых aliases.
Обычный pytest
его пропускает; этот skip не означает выполненный integration run.

Официальный [Model Registry workflow](https://mlflow.org/docs/latest/ml/model-registry/workflow/)
проверен 2026-10-11: database backend, explicit versions и aliases. В MLflow 3
logged-model identity также отличается от run ID. Наш adapter проверен на 3.17.0;
новая minor version требует собственного runtime replay.
