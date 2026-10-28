# Контейнер существующего CPU API: build → HTTP → restart → reload

Prerequisites: [готовый A1 bundle](../../../projects/document_intelligence_lab/part_a1/README.md),
[локальный CPU API](../../../projects/document_intelligence_lab/service/README.md),
этот [Docker-урок](README.md) и [SQL-вход](../07_postgresql/sql_basics.md).
Переиспользуем **существующий** API и Dockerfile. Нового сервиса и учебного web app нет.

**Состояние 28.10.2026: материал подготовлен; container build/run NOT_RUN.**
В текущей Windows-среде `docker` не найден, Linux/WSL не предоставлен. Ничего не
устанавливалось и не скачивалось. Пройти Python/SQL можно сейчас; реальный runtime
этап возвращается после появления явно выбранного Docker/Linux окружения.
Наличие Dockerfile или зелёный TestClient не означает успешный Docker build.

## Сначала интуиция и прогноз

Локальное приложение уже читает сохранённые модель и preprocessing при запуске.
Контейнер нужен, чтобы запускать этот код с его зависимостями в выбранном окружении.
Это не обучение и не исправление качества модели. Если после restart изменится
контрольный ответ, что проверять: модельные байты, конфигурацию, версии или только имя образа?

- **Образ (image)** — шаблон файлов/команды запуска. Tag — изменяемое имя;
  `docker image inspect ... .Id` показывает выбранную локальную identity.
- **Контейнер (container)** — работающий или остановленный процесс с файловой
  средой из образа. Linux-контейнеры используют Linux kernel; на Windows для этого
  обычно нужна предоставленная Linux VM/WSL-среда. Здесь её не создаём.
- **Порт (port)** связывает host endpoint с портом процесса. `EXPOSE 8000`
  документирует намерение, но не публикует порт. Публикация — отдельный `-p`.
- **Bind mount** показывает выбранный каталог host внутри контейнера. Модель
  не должна случайно пропасть при пересоздании контейнера; используем отдельный
  неизменяемый bundle и read-only mount. Секреты/данные не включаем в build context.

```text
Dockerfile + lock + разрешённый код → build → image ID
                                               │ run
host 127.0.0.1:18000 → container :8000 → API startup → verify+load → /ready
                                               ↑
host rules bundle ── read-only /bundle ──────────┤
operator config ── read-only /config/service.json┘

restart: процесс остановлен → новый startup → повторная проверка bytes → load
remove/recreate: writable слой исчезает; host bundle остаётся
```

У модели нет «магической памяти», переживающей restart. Программа заново читает
выбранные байты. `readonly` ограничивает запись из контейнера, но не защищает от
подмены файлов на host; оператор должен защищать host каталог. Digest связывает
байты, а не доказывает качество и безопасность недоверенного pickle.

## Подготовка без Docker

Из корня в PowerShell, output должен быть **новым**:

```powershell
uv run python -m projects.document_intelligence_lab.service prepare-teacher --output artifacts/container-practice
uv run pytest projects/document_intelligence_lab/service -q
```

Готовая команда создаёт `rules/manifest.json`, host config и `container-service.json`.
Последний уже содержит `bundle_root=/bundle` и digest реальных bytes; его не надо
придумывать или исправлять под ошибочную модель. Правила в JSON выбраны для безопасного
первого запуска без executable serialization. Учительский классификатор знает
`circle/square`, неизвестный `triangle` относит к `circle`: это ограничение baseline.

Эта подготовка и ASGI tests проверяются на host. Они не проверяют доступ к registry,
build toolchain, архитектуру image, mounts, разрешения UID или опубликованный HTTP порт.

## Только на уже предоставленном Docker runtime

Следующие команды — **явные действия ученика**, автоматически не вызываются тестами.
Build при отсутствии cache может скачать базовые images и locked Python dependencies;
решение о таком сетевом запуске принимается отдельно. Не делайте вывод «готово» до
выполнения всех шагов и сохранения их результата. Команды ниже пока не исполнялись.

```powershell
docker version
docker info
docker build --pull=false -t roadmap-cpu-practice -f projects/document_intelligence_lab/service/Dockerfile .
```

Контекст build — корень repo, не папка Dockerfile. Его существующий
[allowlist](../../../projects/document_intelligence_lab/service/Dockerfile.dockerignore)
пропускает только runtime code/lock, а student data/output не копирует.
`--pull=false` не даёт гарантии полностью offline build: отсутствующий base или
пакеты всё ещё потребуют сеть. Сохраните image identity и paths:

```powershell
$imageId = docker image inspect roadmap-cpu-practice --format '{{.Id}}'
$bundlePath = (Resolve-Path 'artifacts/container-practice/rules').Path
$configPath = (Resolve-Path 'artifacts/container-practice/container-service.json').Path
$expected = (Get-Content -Raw $configPath | ConvertFrom-Json).expected_manifest_sha256
docker run --name roadmap-cpu-practice --pull=never -d -p 127.0.0.1:18000:8000 --mount "type=bind,source=$bundlePath,target=/bundle,readonly" --mount "type=bind,source=$configPath,target=/config/service.json,readonly" $imageId
```

Имя контейнера должно быть свободным: не удаляйте чужой экземпляр ради этой команды.
Это JSON-rules factory, не произвольный sklearn loader. Для другого executable bundle
нужны отдельные operator trust и версия-согласованность: прежний урок уже объясняет их.
Порт публикуется только на loopback. Внутри контейнера Uvicorn слушает `0.0.0.0`,
чтобы проброс порта работал; это не повод публиковать host порт на всех интерфейсах.

## Фактический HTTP smoke и reload

После запуска дождитесь readiness; если запрос ещё не проходит, смотрите logs,
а не переписывайте digest. В новом контейнере доступ к mount может отличаться от host.

```powershell
docker logs roadmap-cpu-practice
$before = Invoke-RestMethod 'http://127.0.0.1:18000/ready'
if (-not $before.ready -or $before.bundle_sha256 -ne $expected) { throw 'Wrong readiness identity' }
$prediction = Invoke-RestMethod 'http://127.0.0.1:18000/predict' -Method Post -ContentType 'application/json' -Body '{"text":" SQUARE "}'
if ($prediction.predicted_label -ne 'square' -or $prediction.bundle_sha256 -ne $expected) { throw 'Wrong prediction or identity' }
docker restart roadmap-cpu-practice
```

После restart снова дождитесь успешного `/ready`, выполните **те же** проверки
`/ready` и `/predict`, сравните identity/label с `$before` и `$prediction`.
Запишите container ID, image ID, bundle digest, реальные ответы, время ожидания и
результат проверки. Пока запрос во время startup не обслуживается — это нормальное
отсутствие готовности, а не основание игнорировать дальнейшую ошибку загрузки.

| Этап | Ожидаемая проверка | Что это доказывает |
| --- | --- | --- |
| build | exit 0 и локальный image ID | образ построился на этой платформе |
| run | процесс запущен, /ready с ожидаемым digest | bundle проверен и загружен |
| HTTP | square + тот же digest | валидация/маршрут/inference работают |
| restart | новый startup + те же bytes/ответ | модель повторно загружена из mount |
| remove/recreate | собственный контейнер пересоздан с теми же mounts | состояние зависит от bundle, не writable слоя |

Для последнего шага, **только для созданного вами** имени:

```powershell
docker stop roadmap-cpu-practice
docker rm roadmap-cpu-practice
```

Повторите прежний `docker run` с тем же `$imageId`, проверьте HTTP и identity,
затем остановите/удалите собственный контейнер этими же двумя командами.
Host bundle сохраните для отчёта; очистка чужих containers/volumes не нужна.

## Типичные ошибки и самостоятельная вариация

Ошибка: включить `.venv`, `.env` или весь рабочий каталог в image; выдавать `EXPOSE`
за публикацию порта; менять files/digest вместе после повреждения; считать restart
проверкой нового image; проверять только HTTP 200 без model identity.

Самостоятельно выберите **свой** ранее проверенный JSON-rules bundle и новое имя
контейнера/host port. До запуска нарисуйте путь запроса и пути mount. Проведите
build → HTTP → restart → recreate. В отдельной **копии** bundle измените байт, сохранив
исходный expected digest: новый startup должен отказать. Исходный bundle не портите.
Для восстановления выберите исходные защищённые bytes/config, а не пересчитайте hash
из повреждённого экземпляра. Выводы и отчёт должны быть ваши, шаблон ответа не заполнен.

Done для **материала**: объяснения и маршрут готовы. Done для **вашего опыта**:
сохранён журнал реальных команд/identity/HTTP/restart/recreate/ошибки/recovery,
и вы объясняете, какие байты/состояния переживают перезапуск. Пока runtime отсутствует,
ставьте **NOT_RUN**, а не skip=«освоено». Даже успешный smoke не проверяет нагрузку,
продакшен-безопасность, модельное качество или облачный deployment.

Официальное дополнительное объяснение, английский, проверено 28.10.2026:
[What is a container](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/),
[Bind mounts / read-only](https://docs.docker.com/engine/storage/bind-mounts/).
Остановитесь после image/container и bind mounts; Kubernetes для этого задания не нужен.
