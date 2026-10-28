# Вводный tracking: запись эксперимента и возврат его байтов

Нужны [A1](../part_a1/README.md), [CPU service](../service/README.md),
[experiment protocol](../../../docs/experiment-protocol.md) и понятия
[releases/evaluation](../../../modules/08_production_ai/02_releases_evaluation/README.md).
Задача: различить описание run и сам восстановимый модельный комплект.
Фактический local smoke выполнен 2026-10-11 в отдельной `.venv-tracking`
с MLflow 3.17.0: два runs, sklearn/pyfunc reload, bundle restore и отдельный
[registry promotion/rollback](registry-lifecycle.md). Это авторская синтетическая
проверка механики; качество модели и защита ученика остаются `REQUIRES_REVIEW`.

## Прогноз и механизм

Есть два runs с одинаковым score, но разными seed. Можно ли по score выбрать
файл модели? Если SQLite уцелел, а artifact directory удалён, сохранилась ли модель?
Run — запись эксперимента; artifact — сохранённые байты; model flavor — формат
сохранения/загрузки модели со своим input contract. Эти сущности связаны, но
одна запись не заменяет остальные.

```text
Run A (seed 17)
  ├─ params/metrics/tags → local SQLite (абсолютный путь)
  └─ bytes + sklearn flavor → artifact root / run A
                                    |
                            NEW restore directory
                                    |
                        digest + schema + inference replay
Run B (seed 29)
  ├─ params/metrics/tags → та же local SQLite
  └─ bytes + sklearn flavor → artifact root / run B
```

Пример ручного чтения будущего результата:

| Поле | Откуда получается | Что оно позволяет проверить |
| --- | --- | --- |
| `seed=17` / `seed=29` | config двух реально обученных teacher runs | различие условий, не гарантия разных predictions |
| `accuracy`, `macro_f1`, `count` | пересчитанные сохранённые A1 metrics | размер и арифметика toy оценки, не будущая точность |
| `bundle_sha256` tag | digest completed manifest | какую точную identity надо восстановить |
| `bundle/model.pkl` | байты проверенного fitted pipeline | реальное содержимое; требует явного local trust |
| `model_uri` | результат `mlflow.sklearn.log_model` | reloadable flavor с signature, не полный raw-text сервис |

MLflow backend хранит metadata, artifact store — файлы. Здесь используются
`sqlite:///` + **абсолютный** путь и `Path.as_uri()` абсолютного local artifact root.
Remote URI не является допустимым параметром этого intro. Даже metadata в local
SQLite может ссылаться наружу: перед restore URI run дополнительно проверяется
на containment выбранного artifact root.

## Явная демонстрация после runtime gate

В заранее подготовленной tracking environment выполните из корня команду её Python:

```powershell
.venv-tracking/Scripts/python.exe -m projects.document_intelligence_lab.tracking_intro.demo --output artifacts/r04-tracking
```

Имя environment соответствует [compute guide](../../../docs/compute-guide.md);
каталог должен быть подготовлен заранее отдельным разрешённым шагом. Команда
не устанавливает пакет, не обновляет sklearn/Torch и не запускает UI/server.
Не используйте `--all-groups`. Подготовленная environment прошла actual smoke;
новая машина требует своей явной подготовки runtime. В base environment вызов
того же модуля явно выдаёт `NOT_RUN: MLflow runtime missing` до создания output.

Когда gate пройден, `run_demo(NEW_PATH)` действительно:

1. Создаёт два независимых A1 teacher запуска с seed 17 и 29, выбирает их
   sklearn bundles, проверяет manifests/байты и actual reload predictions.
2. Создаёт local experiment с фиксированным artifact location. Каждый run пишет
   params/metrics/tags и только allowlist файлов bundle; соседние файлы не логируются.
3. Логирует настоящий sklearn model flavor, signature и input example, затем
   реально загружает flavor и сравнивает predictions. Pip requirements заданы
   из текущих версий bundle; автоматический infer/install dependencies не нужен.
4. Восстанавливает run 17 в **новый** каталог через MLflow artifact API, проверяет
   expected manifest digest и реальные test predictions уже из восстановленного
   bundle. `tracking.json` появляется лишь после успешного завершения этих действий.

Полные raw texts обрабатываются `predict_documents` из bundle. Сохранённый sklearn
flavor ожидает **уже нормализованные** строки (`unicode-whitespace-v1`), поскольку
внешняя NFKC/casefold/whitespace обработка является отдельным контрактом A1.
Signature — одномерный string tensor: для `mlflow.pyfunc` передайте
`numpy.array(normalized_texts)`, для sklearn flavor — последовательность строк.
Проверка настоящим runtime обнаружила, что signature, выведенная из Python list,
превращала input в DataFrame, и TF-IDF получал номер колонки вместо документа.
Tensor signature исправляет эту границу. Signature не реализует preprocessing. Для raw-text service
восстанавливайте весь bundle и используйте общий loader; JSON metrics alone не
являются reloadable model. Registry с alias/version и promotion выполняется в
[локальном продолжении](registry-lifecycle.md); общий контекст —
[lifecycle lab](../../../labs/06_ml_lifecycle/README.md).

Для подключения намеренно выбранного локального bundle есть
`track_bundle(bundle_root, expected_manifest_sha256, *, database, artifact_root,
experiment_name, trusted_local_artifact=False)`. Доверие по умолчанию выключено;
никакого сканирования pickle каталогов. `restore_run_new(run_id, NEW_PATH, *,
expected_manifest_sha256, database, artifact_root, trusted_local_artifact=False)`
также требует operator selection и проверяет локальность bytes до чтения.
Запуск на существующий output отказывает: история эксперимента не перезаписывается.

## Разбор отказа и самостоятельная вариация

До чтения ответа предскажите, что произойдёт, если восстановить правильные model
bytes с preprocessing другой версии. Contract validation отвергнет bundle;
обновление только `model_id` не исправляет несовместимость. Если metadata доступны,
а artifact bytes потеряны, восстановление не доказано: выберите проверенную
резервную копию и сохраните причину отказа, не создавайте «успешный» run вручную.

В собственной работе выберите два осмысленно различающихся config/метода своей
A1 модели, одинаковые splits и независимый output. Объясните, почему различие
seed может не изменить predictions; проверьте восстановление одного bundle и
его raw-text API. Оставленный [report template](report-template.md) заполняется
собственными наблюдениями, не teacher результатами.

Шесть вопросов: что хранит SQLite? Где лежат байты модели? Почему одинаковый
score не означает одинаковый bundle? Что доказывает flavor reload и чего не
доказывает? Почему local tracking URI не гарантирует local artifacts? Какая
проверка после restore обнаружит несовместимый preprocessing?

Base unit checks проверяют URI boundary и ясный missing-runtime отказ. Они не
подменяют MLflow и не засчитывают два runs. ASGI recovery smoke выполняется
отдельно в service. MLflow round trip, registry, container/cloud, ML quality и
защита ученика имеют отдельные статусы. Локальный tracking/registry smoke исполнен;
container/cloud и защита ученика этим результатом не подтверждаются.

Есть явный integration gate `test_optional_round_trip.py`: по умолчанию он
пропущен с причиной NOT_RUN. Только в заранее подготовленной tracking environment
разрешённый запуск выполняется так (environment variable действует на этот терминал):

```powershell
$env:ROADMAP_RUN_MLFLOW = "1"
.venv-tracking/Scripts/python.exe -m pytest projects/document_intelligence_lab/tracking_intro/test_optional_round_trip.py -q
Remove-Item Env:ROADMAP_RUN_MLFLOW
```

Этот тест вызывает настоящий MLflow, два обучения/logging, sklearn/pyfunc reload,
restore и registry rollback. Socket connections запрещены fixture; `_mlflow()`
до импорта принудительно задаёт `MLFLOW_DISABLE_TELEMETRY=true`, потому что SDK
по умолчанию допускает telemetry. При отсутствующем runtime тест падает.
Защитите SQLite, artifact root и operator config от посторонней записи:
digest подтверждает байты, но не превращает pickle в безопасный формат.

## Источники и остановка

Официальная документация проверена через веб 2026-10-11, английский:
[Tracking quickstart](https://mlflow.org/docs/latest/ml/tracking/quickstart/) —
manual start_run/log params/metrics/model и reload;
[sklearn API](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.sklearn.html) —
`log_model(name=..., signature=..., pip_requirements=...)` и `load_model`;
[artifact API](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.artifacts.html) —
`download_artifacts` с run ID и явно выбранной local destination;
[backend](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/) и
[artifact store](https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/) —
различие SQLite и файлов. Остановиться перед remote server/registry deployment.
Установленный MLflow 3.17.0 проверен отдельно настоящими CLI и integration tests.
