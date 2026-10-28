# A1 → локальный CPU API → восстановление

После [A1](../part_a1/README.md) у модели уже есть воспроизводимый bundle.
Теперь нужно доставить **тот же** preprocessing и модель в API, проверить отказ
при несовместимом запуске и восстановить прежнее поведение. Нужны
[FastAPI](../../../modules/02_python_backend/01_fastapi/README.md),
[Pydantic](../../../modules/02_python_backend/02_pydantic/README.md),
[интеграционные тесты](../../../modules/02_python_backend/08_api_integration_testing/README.md)
и [протокол эксперимента](../../../docs/experiment-protocol.md).
Учительский пример синтетический; свои A1 материалы подключайте отдельно.

## Сначала прогноз

Учительское правило знает `circle` и `square`, а неизвестное относит к `circle`.
Вторая модель — обученный на train TF-IDF + LogisticRegression. Что вернёт
`{"text":"triangle"}` до смены модели, после неё и после отката? Если после
отката вернуть только имя `A`, а preprocessing оставить от B, достаточно ли этого?

Bundle похож на запечатанный комплект: модель, её обработка текста, порядок
меток, версии библиотек и проверочные данные. SHA-256 связывает точные байты
комплекта. Он не доказывает качество и не делает чужой pickle безопасным.
Оператор защищает каталог и конфигурацию от одновременной подмены; это граница
доверия, а не изолированная среда исполнения недоверенного Python.

```text
Оператор: local Path + digest + явное доверие
                       |
               startup: verify + load
                       |
             replay test cohort → ready
                                      |
Запрос: только text → validation → saved preprocessing → модель bundle
                     тип/непустота/                     |
                     1..10000 символов     label + model ID + version + digest
```

Startup (запуск) завершается до readiness (готовности). При плохом bundle
lifespan выбрасывает ошибку и сервер не начинает обслуживание. `/ready` без
загруженной модели и `/predict` до lifespan возвращают 503. Готовность означает
механическую проверку сохранённых test предсказаний, а не качество на будущем трафике.
Shutdown (остановка) снимает готовность. Каждый новый запуск проверяет файлы снова.

HTTP запрос принимает ровно `{"text": string}`: лишние поля, числа вместо строки,
пустая/пробельная строка и длина свыше 10000 отвергаются с 422. Нельзя прислать
путь, URL, ground truth, доверие или загрузить новую модель в `/predict`.
Функция `predict_documents` дополнительно защищает внутренний batch-контракт.
Ограничение текста не является общим ограничителем размера HTTP body или очереди:
для внешнего deployment такие лимиты задаются отдельно на ingress/server.

## Запуск учительского примера

Из корня репозитория, с существующей `.venv`; без установки, сети и Docker:

```powershell
.venv/Scripts/python.exe -m projects.document_intelligence_lab.service prepare-teacher --output artifacts/r04-teacher
.venv/Scripts/python.exe -m projects.document_intelligence_lab.service serve --config artifacts/r04-teacher/service.json
```

Первая команда создаёт **новый** каталог и операторский config с настоящим
абсолютным путём и digest. Существующий output не перезаписывается. Вторая
явно запускает Uvicorn только на `127.0.0.1:8000`; остановите Ctrl+C.
Import `app.py` сервер не запускает. Из второго терминала:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/ready
Invoke-RestMethod http://127.0.0.1:8000/predict -Method Post -ContentType application/json -Body '{"text":"  SQUARE\n"}'
```

Результат содержит `predicted_label=square`, `model_id=a1-rules`,
`preprocessing_version=1` и `bundle_sha256`, равный digest в созданном config.
Поле digest каждый раз читается из реально созданного запуска, а не копируется
из примера. Сравнение по шагам:

| raw text | NFKC → casefold → collapse whitespace | A rules | B TF-IDF |
| --- | --- | --- | --- |
| `  SQUARE\n` | `square` | `square` | `square` |
| `triangle` | `triangle` | `circle` | `triangle` |
| пробелы | запрос отвергнут до inference | 422 | 422 |

Смените вход на `triangular`: правило не знает синонима. Предскажите ответ до
проверки. Нормализация не выполняет перевод или смысловое понимание.

Публичные функции: `create_app(Path, expected_manifest_sha256, *,
trusted_local_artifact=False)` и `create_app_from_config(Path, *,
trusted_local_artifact=False)`. Config содержит ровно `bundle_root` (абсолютный
локальный путь) и `expected_manifest_sha256`. Factory для Uvicorn читает путь
config из `ROADMAP_SERVICE_CONFIG`; готовый teacher config не требует правки.
Для сознательно выбранного собственного sklearn bundle оператор передаёт
`serve --config ... --trusted-local-artifact`. Совпадение hash не заменяет это
решение. JSON rules загружаются без executable serialization.

## A → B → отказ → A: измеренная демонстрация

```powershell
.venv/Scripts/python.exe -m projects.document_intelligence_lab.service.recovery --output artifacts/r04-recovery --samples 5
```

`recovery.json` хранит сырые HTTP status, длительности **в секундах**, условия,
sample count, batch size, версии, ошибку startup и полную identity каждого
ответа. `timeline.svg` строится из этих наблюдений. Последовательность:

| Состояние | Проверяемое действие | Наблюдаемое поведение |
| --- | --- | --- |
| A | новый lifespan rules bundle | `triangle → circle` |
| B | остановка A, новый lifespan TF-IDF bundle с явным доверием | `triangle → triangle` |
| отказ | новый startup B с неправильным digest | ValueError, запросы не обслуживаются |
| A-restored | новый app и lifespan из полного исходного A bundle | `triangle → circle`, исходная identity |

Это реальные ASGI startup/inference/close через `TestClient`, без сетевого
сервера и контейнера. Здесь откат — явный выбор прежнего неизменённого bundle;
восстановление утерянных файлов из MLflow разобрано [отдельно](../tracking_intro/README.md).
Скрипт не меняет alias или «активную версию» вместо вызова модели.

Медиана — центральная длительность отсортированных запросов, максимум — самая
длинная **наблюдавшаяся**. Пятнадцать последовательных запросов не оценивают p99,
конкурентную нагрузку или production SLO. Startup включает загрузку и replay,
HTTP timing включает TestClient/валидацию/сериализацию. Все inference samples
помечены `warm_after_startup_replay`: loader уже вызвал модель до readiness.
Отдельное поле `request_position` различает первый HTTP запрос и последующие;
первый HTTP запрос не выдаётся за cold model inference. Память `null`: CPU peak
не инструментирован; GPU и VRAM здесь не измерялись. На графике ось длительности
в миллисекундах, подпись задаёт линейную шкалу 200 px = максимальная длительность;
JSON сохраняет исходные секунды.

Минимальный runbook: остановить неисправный процесс; проверить защищённый config
последнего принятого A; запустить **весь** bundle A; дождаться `/ready`; запросить
контрольный текст и сверить label и все версии с исходным A; только затем вернуть
трафик. Проверка digest после изменения модели должна отказать. Не пересчитывайте
ожидаемый hash из повреждённого каталога как способ «починить» запуск.

## Контейнер: конфигурация, статус NOT_RUN

Image — сохранённая среда с кодом; container — запущенный процесс из image;
service — доступный контракт плюс жизненный цикл. Основы и lock уже разобраны в
[Docker-уроке](../../../modules/02_python_backend/09_docker_delivery/README.md).
Здесь одна конкретная конфигурация: non-root UID 10001, readonly bundle/config,
loopback port на хосте, без модели, секретов или student результатов в image.
`Dockerfile.dockerignore` — allowlist build context; не заменяйте его `COPY . .`.
Копируется только checksum helper как namespace package: полный
`roadmap_tools.__init__` импортирует test adapter/pytest и для runtime не нужен.
Корневой `uv.lock` используется без dev/опциональных групп и без Torch.

После отдельного согласования Docker build/pull/run, из корня, с уже созданным
`artifacts/r04-teacher` (показанные команды в этой работе **не запускались**):

```powershell
docker build -f projects/document_intelligence_lab/service/Dockerfile -t roadmap-document-cpu:r04 .
$r04Bundle = (Resolve-Path artifacts/r04-teacher/rules).Path
$r04ContainerConfig = (Resolve-Path artifacts/r04-teacher/container-service.json).Path
docker run --rm --name roadmap-document-cpu --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=16m -p 127.0.0.1:8000:8000 --mount "type=bind,src=$r04Bundle,dst=/bundle,readonly" --mount "type=bind,src=$r04ContainerConfig,dst=/config/service.json,readonly" roadmap-document-cpu:r04
```

Внутри контейнера слушается `0.0.0.0`; публикация хоста ограничена loopback.
Healthcheck обращается к реальному `/ready`. После запуска выполните те же два
HTTP запроса, остановите контейнер и повторите запуск с теми же mount/config;
повредите **копию** bundle и убедитесь в отказе startup. Конфигурация не является
свидетельством выполнения этих действий. Tag `python:3.12.15-slim-bookworm`
выбран из официального списка; digest image не проверялся и не придумывался.
Build требует отдельно разрешённого доступа к registry/package index; здесь его
не было. Linux compatibility lock и container smoke пока NOT_RUN.

## Самостоятельный перенос и проверка

Откройте [transfer](transfer/README.md); report template оставлен пустым.
Это ручная защита, нового catalog ID нет. Teacher tests не засчитывают работу ученика.
Для повторного применения понятий используйте `production-artifact-manifest`,
`production-request-metrics`, `production-rollout-decision` из
[module 08](../../../modules/08_production_ai/README.md).

Шесть вопросов: почему startup проверяет digest до deserialization? Почему
hash не разрешает доверять pickle? Где живёт train-fitted preprocessing? Почему
422 отличается от not-ready 503? Какая проверка доказывает возврат поведения A?
Что нельзя заключить из медианы пятнадцати запросов?

Unit проверяет границы запроса/конфига; integration smoke запускает реальные
lifespan/inference/reload; ML quality требует отдельной оценки A1; defense
требует объяснения и изменения условия. Docker/cloud/vLLM/полный lifecycle этим
примером не закрываются.

## Источники и границы чтения

Проверены по официальной веб-документации 2026-10-11, язык английский:
[FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) — читать
load/yield/shutdown, остановиться перед альтернативными legacy events;
[Docker Python Official Image](https://hub.docker.com/_/python) — supported tags
и slim image;
[Astral uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/) — locked
sync и intermediate layers. Это проверка документации, а не container execution.
