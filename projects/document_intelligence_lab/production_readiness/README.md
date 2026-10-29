# Production readiness: настоящий HTTP lifecycle

ID: `production-service-lifecycle` · самостоятельное упражнение.
Пререквизиты: `part_a1` (bundle, train/validation/test), существующий `service`,
Python context manager/subprocess, HTTP коды, futures и ограничение параллелизма.
Результат: ученик умеет доказать, какая модель реально обслуживает запросы,
измерить поведение при нагрузке и восстановить предыдущую версию.

## Теория: от Spring lifecycle к ML сервису

В Spring singleton создаётся при старте приложения. Здесь ASGI lifespan загружает
bundle один раз на процесс: проверяет внешний manifest digest, файлы, версии и
воспроизводит сохранённые test predictions. `/ready` становится доступным после
этого. Это механическая готовность, а не доказательство качества на новых данных.
Uvicorn workers — отдельные процессы с отдельными копиями модели и памяти.
Увеличить workers означает также увеличить память и количество параллельных
вычислений; для этого упражнения нужен один worker.

Обучение и serving используют `contracts.normalize_document` через
`artifacts.predict_documents`: Unicode/whitespace версия должна совпадать с
manifest. Нельзя ещё раз написать «почти такой же» preprocessing в endpoint.
Bundle immutable, а config выбирает его по пути и внешнему checksum. Checksum
проверяет целостность, но не делает pickle безопасным: доверие к локальному
sklearn artifact — отдельное решение оператора. Harness доверяет только созданным
им локальным учебным bundles. Не открывайте эту factory для пользовательского
выбора пути/модели. Production JSON rules factory уже есть в `service/app.py`.

Cold в этом эксперименте — запуск нового процесса, импорты, проверка/загрузка
модели, startup replay и первый успешный HTTP readiness. Это не чистое время
первого forward: replay уже прогрел модель. Отдельно сохраняется первый HTTP
predict, затем warm серия. Для чистого cold inference нужен другой протокол с
инструментацией loader; нельзя переименовать эти числа и утверждать, что он измерен.

Клиенты отправляют запросы через TCP на `127.0.0.1`, одновременно работает не более
`concurrency` потоков. ThreadPoolExecutor здесь используется для блокирующего
HTTP I/O; он не ускоряет Python CPU вычисления автоматически. В ASGI синхронный
endpoint исполняется в серверном thread pool. Для тяжёлого CPU inference следует
измерять процессную конкуренцию и oversubscription BLAS, прежде чем повышать workers.
Асинхронная альтернатива требует semaphore и `finally`/TaskGroup для очистки задач.

Каждая попытка имеет outcome, статус и elapsed seconds. HTTP 422 — ответ сервера,
а socket timeout — клиентский deadline; transport_error означает, что ответа не
получено по другой причине. Ошибки не исчезают из denominator. Median/max считаются
по успешным запросам, failure rate — по всем попыткам. Нельзя смешать быстрый 422
с успешной latency и объявить улучшение модели. При 8–12 локальных запросах
наблюдаемый maximum не является оценкой production p99. Дополнительно нужны
wall duration, размер серии, concurrency, окружение, версия модели и код эксперимента.

Клиентский timeout/отмена future не доказывает остановку серверного inference:
поток уже мог начать вычисление. `timeout=1e-9` — намеренный probe для учёта
реального исхода, а не simulation замедленной модели; его исход сохраняется как
наблюдался. Надёжная отмена CPU работы требует кооперации/изоляции процесса и
отдельного контракта. После серии harness terminate/wait каждый дочерний процесс,
при необходимости kill/wait; orphan-процессы не должны оставаться.

Restart проверяет A после нового запуска. Promotion проверяет B по digest,
model_id, preprocessing_version и отличающемуся ответу на один и тот же input.
Некорректный digest должен прервать startup. Rollback запускает неизменённый A и
сравнивает полную identity/предсказание с исходным A. Это локальная последовательная
замена процессов; zero-downtime, load balancer draining и Kubernetes здесь не измерены.

## Мониторинг и delayed labels

Три разных сигнала: доступность/latency/errors; входной drift (длина, язык,
пустые поля, доли источников); качество по присоединённым labels. Drift не доказывает
ухудшение качества. Ошибка сервера также не равна ошибке классификации. Не логируйте
полные документы без необходимости: request_id, время, bundle id, безопасные
агрегаты/длины обычно полезнее персонального текста.

Label приходит позже prediction. При cutoff T доступны только predictions с
`predicted_at <= T` и labels с `available_at <= T`; join по уникальному request_id.
Accuracy = correct / labeled_count, coverage = labeled_count / predictions_count.
При отсутствии labels accuracy = null, а не 0 или 1. Низкая coverage и biased
label arrival ограничивают вывод: сначала разбивайте по возрасту cohort, источнику
и bundle, затем сравнивайте модели. `demo.delayed_quality` показывает этот join,
но не является полноценной системой мониторинга.

Пример заранее объявленных действий (ученик выбирает свои значения до прогона):
5xx > 1% или timeout > 2% за 5 минут при N >= 100 — остановить promotion и
проверить ресурсы; readiness fail — не направлять трафик; сдвиг медианы длины
> 30% — изучить выборку и качество данных; падение macro-F1 > 0.05 при >= 200
доступных labels и сопоставимой coverage — рассмотреть rollback с человеком.
Числа учебные, не универсальные SLO. Tiny synthetic run не подтверждает эти пороги.
В этом harness 422/deadline probes отделены от нормальной warm нагрузки: не включайте
намеренные faults в production failure rate без маркировки.

## Авторский пример (не выполнение упражнения)

Из корня репозитория в подготовленном окружении:

```bash
python -m projects.document_intelligence_lab.production_readiness.demo \
  --output /tmp/production-author-run --requests 12 --concurrency 3
```

В PowerShell замените `/tmp/...` на новый путь внутри `$env:TEMP`.
Выход: `lifecycle.json`, stderr/stdout каждого child, сохранённые bundles.
Авторский пример обучает маленький существующий TF-IDF pipeline локально,
использует общий service app, без скачивания weights и внешней сети.
`AUTHOR_LOCAL_TCP_DEMO` не принимается как learner evidence.
Default pytest не открывает сокеты. Явный runtime smoke при необходимости:

```bash
ROADMAP_RUN_TCP=1 python -m pytest \
  projects/document_intelligence_lab/production_readiness/test_live.py -q
```

Если среда запрещает sockets, этот шаг **NOT_RUN**; выполните на Linux/WSL или
локальном Windows. Не заменяйте его mock/TestClient и не отмечайте runtime credit.
Docker/Linux и один cloud bridge: [deployment.md](deployment.md).

## Самостоятельная работа и required evidence

Реализуйте три функции в `starter.py`, не импортируя author demo.
`test_starter.py` вызывает также сам `run_lifecycle` через socket-free transport seam,
проверяет порядок A/restart/B/rejected/A, configured digests, ограничение load,
ошибку нагрузки и очистку children. Он проверяет независимые summary/delayed-label случаи; успешные
unit tests не заменяют реальный запуск `run_lifecycle` с собственным NEW output.
Используйте свои saved A/B bundles; можно построить их по существующему `part_a1`
контракту. Не меняйте service preprocessing. A/B должны давать разные ответы на
один выбранный probe; restart/rollback A должны совпасть.

Сохраните `lifecycle.json` по схеме author output (`demo.run_demo` показывает
формат, не решение для копирования): schema_version=1, exercise_id, transport,
unit/device, requests_per_stage/concurrency, bundles A/B с relative path и digest,
events A, A-restarted, B, rejected, A-restored. Для успешных stages нужны PID,
startup_seconds, first_request, warm_requests, summary, load_seconds,
fault_probes (invalid input и deadline), fault_summary, cleanup_exit_code.
Каждый request: status, outcome, payload, seconds. `run_status=COMPLETE` нужен
только после всех проверок. При ошибке сохраняйте `run_status=FAILED`,
`failure_reason`, уже завершённые stages и текущий stage с raw outcomes, summary,
`stage_status`, cleanup_exit_code, затем поднимайте исключение. Не теряйте
знаменатель именно в случае overload/timeout. Неполный отчёт не даёт completion.
Rejected stage дополнительно: `bundle_name` (A/B из inventory), configured digest
в `bundle_sha256`, который отличается от сохранённого manifest digest,
`rejection_reason=manifest_digest_mismatch`, `startup_log` с relative path/SHA256.
Лог должен показывать manifest verification/sha256 failure, а не любую startup
ошибку. Successful response имеет ровно predicted_label/bundle_sha256/model_id/
preprocessing_version; все identity поля должны соответствовать saved manifest.
Сохраните логи children.
Дополнительно обязательны:

- `evidence_kind: STUDENT_LOCAL_TCP` и `code_sha256` bytes текущего `starter.py`;
- `analysis`: непустые `cold_warm`, `timeout_cancellation`, `rollback`,
  `delayed_labels`, `threshold_actions` с числами/ограничениями вашего прогона;
- `docker` и `cloud`: `NOT_RUN`, если вы их фактически не выполняли.

### Граница автоматической проверки и защиты

Artifact gate проверяет identity/schema отчёта, `COMPLETE`, ограниченные count и
concurrency, hash текущего starter, наличие пяти полей analysis, bytes/digests A/B,
порядок stages, PID и cleanup exit codes. Он пересчитывает warm/fault summary,
проверяет форму и identity успешных ответов, первый invalid-input probe с 422,
restart/rollback A и отличающийся ответ B. Для rejected startup обязательны
отдельный hash-checked log и сообщение об отказе из-за manifest digest.
Offline learner tests отдельно проверяют запрос короткого timeout и cleanup
через socket-free transport seam.

На защите человек проверяет supporting attachments и их смысл: обычные stdout/
stderr каждого child, команды и исходники запуска, версии Python/пакетов/OS,
CPU/RAM, нагрузку и число workers, а также связь логов с этапами и фактическое
завершение процессов. Он сверяет входы двух fault probes и настроенный deadline
по коду/логам: сохранённые request rows содержат status/outcome/payload/seconds,
но категория входа и численное значение timeout не являются обязательными
полями JSON; второй probe сам по себе не доказывает короткий deadline.
Environment details, обычные child logs и `docker`/`cloud` не являются полностью
машинно проверяемыми полями/вложениями. Человек также оценивает содержание analysis
и честность deployment-статуса; для невыполненных Docker/cloud допустим `NOT_RUN`.
Не фабрикуйте timeout: probe может завершиться успешно, сохраните реальный outcome.

```bash
export ROADMAP_LIFECYCLE_EVIDENCE=/absolute/path/to/your/new-run
python -m pytest projects/document_intelligence_lab/production_readiness/test_starter.py -q
python -m pytest -p roadmap_tools.strict_check \
  projects/document_intelligence_lab/production_readiness/test_starter.py -q
```

PowerShell: `$env:ROADMAP_LIFECYCLE_EVIDENCE='C:\absolute\new-run'`.
Низкоуровневый интерфейс в `transport.py`: `LocalTransport` даёт child context
manager, `ready`, `request`, `load(count, concurrency)`. Это reusable I/O, а не
готовая lifecycle orchestration. В `run_lifecycle(..., transport=None)` выбирайте
LocalTransport по умолчанию; supplied transport используйте для всех I/O.
Самостоятельно реализуйте выбор A/B/digest, порядок stages, проверки identity,
report/failure persistence и работу внутри child context managers. Тестовый
RecordingTransport не открывает sockets; отдельный measured artifact всё равно
обязателен. Сохранённый JSON не заменяет вызов `run_lifecycle` в completion tests.

Нет artifact — default xfail, strict fail. Авторские fixtures и mocked HTTP не
могут закрыть required artifact gate. Валидатор пересчитывает summary, проверяет
bundle bytes и lifecycle identities; JSON/PID/source hash не криптографическое
доказательство реального запуска. На защите нужно показать live rerun и логи.

## Защита и перенос

Слабое доказательство: «pytest зелёный», три screenshots без config, p99 из пяти
запросов, drift объявлен падением accuracy, timeout объявлен серверной отменой.
Сильное: raw outcomes + окружение + digests + полные denominators, отдельные faults,
честная cold definition, воспроизводимый rollback и ограничения delayed labels.
Покажите cold/warm различие, один failure, join запоздалой метки и cleanup процесса.
Перенос: размер модели вырос в 20 раз, labels задерживаются неделю, новая версия
нормализации меняет Unicode. Какие проверки/пороги вы добавите до promotion?
Human review остаётся обязательным даже при `mechanical_status=VERIFIED`.
