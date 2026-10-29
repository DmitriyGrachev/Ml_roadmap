# Самостоятельные измерения vLLM и проверка артефактов

ID: `lab-vllm-measurements`. Prerequisites: [теория serving](../theory.md),
[подготовка среды](../environment/README.md), [явный сбор](../smoke/README.md)
и [протокол измерений](../experiments/README.md). Fine-tuning не prerequisite.

Этот блок добавляет формальную сдачу к уже существующей обязательной vLLM lab.
Текущий реальный запуск **NOT_RUN / DEFERRED_ENV**. Наличие тестов, Linux-инструкции
или заполненного JSON само по себе не подтверждает работающий vLLM на твоём GPU.

## Порядок работы

1. Прочитать [разбор статистики](theory.md), вручную решить маленький пример.
2. Запустить [авторскую арифметику](example.py) и объяснить знаменатель throughput.
3. Самостоятельно реализовать `summarize_measurements` в [starter.py](starter.py).
4. Когда подготовлен Linux/vLLM host, выполнить существующий bounded endpoint
   protocol, сохранить warm-серию и новую серию после перезапуска.
5. Собрать evidence bundle, выполнить строгую проверку и пройти человеческую защиту.

```powershell
uv run --no-sync python -m labs.05_model_serving.assessment.example
uv run --no-sync python scripts/learn.py test lab-vllm-measurements
```

PyCharm: interpreter проекта; pytest target `labs/05_model_serving/assessment/test_starter.py`;
working directory — корень checkout. Эти команды не подключаются к серверу.

## Контракт learner функции

`summarize_measurements(records, *, elapsed_s)` принимает 1..256 записей того же
формата, что `smoke.endpoint`: `request_index`, `status`, `queue_ms`, `e2e_ms`,
`ttft_ms`, `completion_tokens`. Использовать разрешено `protocol.validate_records`
для общей проверки входа, но агрегаты вычислить самостоятельно. Не мутировать вход.

- Индексы уникальны; статусы `ok/error/deadline`; величины конечные, не bool.
- `elapsed_s > 0`; `queue_ms/e2e_ms >= 0`, для `ok` E2E строго положителен;
  `queue_ms + e2e_ms <= 1000 * elapsed_s + 1 ms` (допуск округления).
- `ttft_ms` — null либо число в `[0, e2e_ms]`; токены — null либо целое ≥ 0.
- Вернуть `requests/completed/errors/error_rate`, успешные requests/s и
  `completed_output_tokens_per_s`. Если успешных нет или хотя бы у одного
  успешного запроса нет server usage, token throughput — `None`.
- `latency_ms` агрегирует E2E **успешных** запросов; `ttft_ms` — известные TTFT
  **успешных**. В каждой группе поля `n/min/median/max/empirical_p95`.
  Пустая группа: `n=0`, остальные `None`. При `n<20` p95 — `None`; иначе
  ближайший ранг `ceil(0.95*n)` в отсортированном массиве (индексация с 1).
  Нельзя называть его устойчивой оценкой production p95.

Задание проверяет и все ошибки, и отсутствие usage/TTFT, и нечётные/чётные
выборки. Успешные latency без error rate создают ложное впечатление качества.

## Evidence bundle после реального опыта

Создать **новый** каталог `artifacts/vllm-pa1-my-run/`. Веса/секреты туда не копировать.
`evidence.json` содержит `schema_version: 1`, `status: "RECORDED_REQUIRES_REVIEW"`,
`provider: "vllm"`, `model_repo`, exact 40-hex `model_revision`, `server_model_id`,
`server_command` как массив аргументов и объект `artifacts`.

| Роль в `artifacts` | Содержимое файла |
|---|---|
| `initial` | Оригинальный endpoint JSON warm-серии, ≥2 наблюдений, ≥1 успеха |
| `restarted` | Новый endpoint JSON после остановки/перезапуска, ≥1 успеха |
| `environment` | JSON с `system: "Linux"`, `gpu`, `driver`, `vllm` и подробным inventory |
| `lock` | Собственный resolved serving lock с версиями/источниками |
| `server_log` | Обезличенные startup/readiness/cancellation/restart свидетельства |
| `defense` | Заполненный [отчёт](../experiments/report-template.md) и разбор вариации |

Каждая роль: `{"path": "relative-file-name", "sha256": "hash-of-exact-bytes"}`.
Файлы разные, непустые, максимум 1 MiB каждый, внутри evidence directory.
В `runtime_and_model` обоих endpoint JSON должны совпасть `model_revision`,
`server_model_id`, `runtime_versions.vllm`; значение версии согласовано с environment.
Сохранённые summary пересчитываются из raw. Для проверяемости держать original raw;
не переписывать плохие/неудачные запросы.

```powershell
$env:ROADMAP_VLLM_EVIDENCE = "artifacts/vllm-pa1-my-run"
uv run --no-sync python scripts/learn.py check lab-vllm-measurements
```

На Linux: `ROADMAP_VLLM_EVIDENCE=artifacts/vllm-pa1-my-run uv run --no-sync python scripts/learn.py check lab-vllm-measurements`.
Строгая проверка включает learner arithmetic **и** файлы опыта. Отсутствие пути,
`NOT_RUN`, пропуски и незаполненный starter не дают технический зачёт. Pytest
не поднимает сервер и не получает новые измерения даже с этой переменной.

## Защита и перенос

Проверяющий воспроизводит запуск по lock/команде и проверяет, что работал vLLM:
OpenAI-compatible URL и строка `provider` этого не доказывают. Объяснить cold/warm,
TTFT, completed-output throughput, ограничения sampling памяти, cancellation и
возврат сервера в healthy state. Вариация: изменить **один** параметр контекста,
output cap или concurrency и сопоставить измерения с качеством ответа.

Технический gate проверяет целостность и арифметику, а не подлинность чужих файлов,
авторство кода или GPU совместимость. Финальный статус — **REQUIRES_REVIEW**.
При нехватке среды этот обязательный блок остаётся отложенным; Ollama не заменяет vLLM.
