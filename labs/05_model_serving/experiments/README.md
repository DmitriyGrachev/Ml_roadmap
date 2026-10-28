# Исходные измерения прежде выводов

Реальные model runs/benchmark/peak memory **NOT_RUN**. Здесь нет готового
student report. [Пустой шаблон](report-template.md) копировать в generated
directory только для собственного опыта. [Summary helper](report.py) считает
из переданных raw records; тестовые fixtures явно `synthetic`. Нет сохранённых
вымышленных vLLM результатов и графиков.

## Schema v1 endpoint JSON

| Поле | Смысл/единица и источник |
| --- | --- |
| `evidence` | `live_endpoint`; для unit fixtures `synthetic`; label не доказывает engine |
| `runtime_and_model` | operator manifest: repo/revision/license, tokenizer и files hashes, Linux/runtime/driver/CUDA/lock, server config |
| `model_server_id`, `state`, `concurrency` | exact readiness ID; cold/warm по протоколу; client concurrency 1/2 |
| `request_config` | max_tokens, thinking, temperature, total deadline, request cap, attempts |
| `run_elapsed_s` | monotonic wall seconds от запуска batch до всех результатов |
| `raw[].queue_ms` | client admission wait в ms; server queue отдельно unknown |
| `raw[].ttft_ms` | ms от dispatch до первого непустого answer content; null без него |
| `raw[].e2e_ms` | ms dispatch → DONE/error/close; 0 для не допущенного из очереди |
| `raw[].content_offsets_ms`, `content_deltas_ms` | arrivals и интервалы content chunks; не времена отдельных токенов |
| `raw[].prompt_tokens`, `completion_tokens` | фактический server usage или null; не len(text)/4 и не число чанков |
| `raw[].status`, `error`, `finish_reason` | ok/error/deadline, фиксированная категория (включая protocol при повреждённом content encoding), server reason; усечение length анализировать отдельно |
| `memory_bytes` | null в client report: client не видит server GPU memory |
| `summary` | requests/completed/errors; completed requests/s и tokens/s за wall time |

Тексты ответов и prompts по умолчанию не сохраняются. Для независимой answer
evaluation вести отдельные разрешённые non-sensitive examples, фиксированные
вопросы/критерии и ответы с provenance. Client report не оценивает качество.
Server logs не должны содержать секреты; endpoint body ошибок не логировать.

`completed_output_tokens_per_s` = сумма **server usage успешных запросов** /
`run_elapsed_s`. Если хоть у одного успешного запроса usage отсутствует — null.
Ошибочные partial completions не включаются в numerator; число ошибок видно рядом.
Это completed-output throughput, не decode rate. Decode tokens/s остаётся unknown
до подходящей server token timeline/документированной метрики. Ни количество
SSE events, ни средняя длина слова не заменяют tokenizer evidence.

Пример только арифметики: synthetic records с ok(4 tokens), deadline(null),
ok(6 tokens) за 2 s дают completed=2, errors=1, completed_requests/s=1 и
completed_output_tokens/s=5. [Тест](../test_report_preflight.py) проверяет эти
literal значения и JSON round trip raw → saved summary. Это **не измеренная
скорость Qwen/vLLM** и не student answer evaluation.

## Протокол реального опыта

1. Записать ОС/WSL или native Linux, Python, driver, CUDA runtime, GPU/capability,
   vLLM/PyTorch/FlashInfer/kernel versions, exact resolved lock/hash и CLI output.
   Зафиксировать inputs/tokenizer revision/template/stop tokens и generation params.
2. Подтвердить подготовленный snapshot/kernels без outbound сети. После startup
   записать baseline память, готовность и первый короткий запрос: cold, 1 request.
   Не смешивать model load seconds и TTFT работающего server.
3. Провести warm с тем же prompt/config, concurrency 1, четыре коротких запроса;
   затем concurrency 2 только если безопасно, с новым server_config. Общий cap 8
   на вызов клиента; повторения ограничены заранее и отдельны в отчёте.
4. Отдельный cancellation опыт: увидеть first content, отменить request, сохранить
   client close + server abort/последующий healthy запрос. Проверить deadline,
   overload rejection и malformed provider failure собственными tests без сети.
5. Остановить процесс, повторить команду из того же snapshot/lock, повторно проверить
   model id и readiness/stream. Для смены модели остановить предыдущую, дождаться
   освобождения GPU и начать отдельную серию, не три модели сразу.

У первых smoke мало samples: не делать вывод о production p95 или стабильном
ускорении. Достаточно показать raw точки с подписями axes `request index` /
`TTFT or E2E, ms`, cold/warm/concurrency/error. Строить график только из своего
сохранённого JSON, при unknown token count не рисовать token-rate bar.
Для сравнения моделей одинаковы тексты, но tokenizer counts записываются заново.
Сокращение контекста/ответа — изменение задачи; повторить quality evaluation.

## Память и типичные ошибки

`nvidia-smi` показывает MiB устройства/процессов; умножить на `2^20`, если
переносите в schema bytes. Нужны timestamp, baseline, peak и sampling interval,
а также какие процессы включены. Периодический sampling может пропустить peak;
вывод так и ограничить. PyTorch allocated/reserved — иной источник, не заменяет
device used. Клиент сам эти данные не меряет: без evidence оставить null/unknown.

0.65 × 8151 MiB ≈ 5298 MiB — лишь стартовая доля memory budget экземпляра,
не измеренный peak и не гарантия свободной памяти. KV pool/activations/kernels
и другие процессы влияют на fit. OOM либо невозможность concurrency 2 — результат
с конфигурацией и отказом, не повод бесконтрольно поднимать utilization.

Ошибка: суммировать перекрывающиеся E2E в denominator batch throughput.
Ошибка: сравнить cold одной модели с warm другой. Ошибка: назвать content-chunk
interval межтокенным. Ошибка: отметить `real vLLM` только по OpenAI-compatible URL.
Ошибка: заменить mandatory vLLM на Ollama/HF при нехватке среды.

Материалы и transport tests — author evidence. Реальный runtime требует Linux
GPU execution, а освоение ученика — собственная [вариация](../variation.md)
и защита / REQUIRES_REVIEW.
