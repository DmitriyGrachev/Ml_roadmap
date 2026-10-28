# Явный smoke существующего endpoint

Текущий реальный запуск — **NOT_RUN**. Этот клиент ничего не устанавливает и
не запускает vLLM. Сначала оператор выполняет [environment gates](../environment/README.md)
и сам поднимает сервер. Windows base httpx уже установлен; использовать явный
интерпретатор, не пересинхронизировать serving/training environments.

Из корня курса, только после разрешённого server startup, например PowerShell:

```powershell
.venv/Scripts/python.exe -m labs.05_model_serving.smoke.endpoint --live --endpoint http://127.0.0.1:8000/v1 --model local-qwen3-06b --manifest C:/serving-evidence/manifest.json --state cold --requests 1 --concurrency 1 --output C:/serving-evidence/cold-01.json
```

Пути — выбранные оператором существующие directories с новым output filename,
не файлы этого пакета. Linux: заменить interpreter на подготовленный client Python.
Manifest нужен клиенту как metadata; он содержит paths Linux, но Windows клиент
не открывает Linux weights/cache. В нём обязательны model revision, совпадающий
server model id и runtime versions. Полный Linux preflight выполняется **на сервере**.

Без `--live` команда выходит 2 / NOT_RUN до создания HTTP client. URL ограничен
HTTP loopback `/v1`: `localhost` нормализуется в `127.0.0.1`, допустим `::1`;
auth/query/fragment и нелокальные адреса отклоняются. Redirects и environment proxies
отключены. Нет аргумента обхода loopback: для native remote Linux сначала нужен
явно разрешённый закрытый tunnel, который предоставляет локальный endpoint.
Связность Windows ↔ WSL localhost проверяется отдельно; не расширять bind до
`0.0.0.0` для исправления smoke.

Сначала streamed GET `/models`, максимум 10 s ожидания и 1 MiB сохранённого body;
превышение останавливает чтение до накопления следующей порции и закрывает response.
Readiness запрашивается с `Accept-Encoding: identity`; compressed readiness
отклоняется по headers **до чтения/декодирования**, чтобы decompression expansion
не обходил budget. Exact model id должен быть в списке.
Затем конечный batch: 1..8 запросов, active concurrency 1 или 2, deadline 30 s
включая локальную очередь, максимум 128 output tokens, 8192 bytes prompt,
64 KiB SSE record и 1 MiB stream. Число **попыток один**, retries ноль.
Teacher prompt нейтральный фиксированный; тексты/секреты не пишутся в report.
SSE role/usage/reasoning events не начинают answer TTFT; missing DONE — ошибка.
Повреждённое HTTP content encoding в SSE даёт фиксированный `protocol` error,
включая повреждение после partial content; исключение decoder не теряет raw result.
При partial failure сохраняется status/error/timing, ответ не replayed.

Успех exit 0, завершённый опыт с request errors exit 1 и сохранённым raw report;
ошибка input/readiness/connection/output exit 2. HTTP/provider bodies и endpoint
credentials не выводятся. Существующий report не перезаписывается.
Ctrl+C/отмена закрывает response; server-side abort/release доказать отдельно.

Сначала cold=первый запрос после процесса startup; затем новый filename и
`--state warm --requests 4 --concurrency 1`. Cold label задаёт оператор, клиент
не может доказать отсутствие предшествующего запроса. После проверки памяти
изменить server max-num-seqs на 2, сохранить новый config/restart и снять
`--concurrency 2`. Не считать client concurrency=2 доказательством server batch=2.
Длинные стресс-тесты не нужны. Недостаток памяти фиксируется как ограничение.

`evidence=live_endpoint` означает настоящие HTTP measurements в данном опыте,
**не автоматическое подтверждение vLLM**: любой совместимый сервер способен
ответить на эти URL. Для зачёта приложить Linux process/CLI/version/GPU evidence,
lock, snapshot inventory и restart. Synthetic pytest reports никогда не меняют
этот статус. [Формат и анализ измерений](../experiments/README.md).
