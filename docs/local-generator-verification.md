# Первый реальный локальный генератор — 28.10.2026

Использована существующая Windows Ollama 0.40.11 и уже сохранённая
`qwen2.5:latest`, 7.6B Q4_K_M. Downloads, installs и изменения зависимостей — отсутствуют.
Это teacher experiment поверх **lexical retrieval**, не полный dense R07 и не зачёт.

## Что действительно произошло

Проверены SHA256 и размеры всех шести cache blobs, включая модель 4 683 073 952 bytes.
Внешний manifest SHA256:
`156bcbf71df68f7a6581fb4ab306ed921b8114d82b6eaeab5c0442785ea9b4c3`.
Ollama возвращает digest вложенного manifest:
`845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`.
Именно второй используется для server identity до и после запроса.
Первая попытка безопасно остановилась **до генерации** из-за сравнения разных
manifest identities; ошибка исправлена с отдельным RED→GREEN тестом, без смены модели.

| Случай | Фактический результат | Вызов модели |
| --- | --- | --- |
| `scanner settings` | `use 300 dpi for paper copies`, citation `A-SCAN@1:p1` | Один |
| `volcano insurance` | `no_answer`, пустые citations | Нет |
| scanner после перевода источника в staff | `no_answer`, пустые citations | Нет |
| тот же ответимый вопрос после остановки server | `provider_error`, пустые text/citations | Одна неудачная попытка соединения |

Первый непустой content (TTFT): **36 703 ms**, end-to-end **38 156 ms**.
Это один запрос с загрузкой модели, **не** warm latency benchmark/p95/concurrency.
Server usage: **135 prompt tokens / 25 completion tokens**; finish reason `stop`.
После запроса `/api/ps`: context length 2048, runner `llamacpp`,
`size_vram=4 635 859 352 bytes`. Это server-reported allocation, не peak GPU memory.
RTX 5060 Laptop: 8151 MiB total; один `nvidia-smi` snapshot после опыта — 6222 MiB used
всей системой, не выделенное потребление только модели.

Сохранены точный prompt с разрешённым passage, его SHA256, ответы, stream timings,
usage, конфигурация, версия runtime, digest до/после:
`artifacts/local-generator-20261028/experiment-identity-fixed/receipt.json`.
Сырые logs и неудачный receipt сохранены рядом в ignored artifacts. Там нет staff текста.
Отдельный `provider-unavailable.json`: реальный transport error, E2E 2047 ms,
без искусственной подстановки ответа и без повторной попытки.
Тестовый сервер и его дочерние процессы остановлены; публичного listener не создавалось.

## Как повторять отдельно от pytest

Из корня репозитория, только если выбранная модель уже находится в cache:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_CONTEXT_LENGTH = '2048'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_NOPRUNE = '1'
& "$env:LOCALAPPDATA/Programs/Ollama/ollama.exe" serve
```

В другом терминале, **новая** output-папка:

```powershell
.venv-base-check/Scripts/python.exe -m labs.03_real_rag.local_generator --run-local --output artifacts/local-generator-my-run --model-digest 845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e
```

Команда не запускает server, не делает pull и не выбирает другую модель.
Несовпадающий digest, неполный SSE, length finish, timeout или плохой JSON не дают PASS.
Output никогда не перезаписывается. После опыта остановите собственный server через Ctrl+C.
Обычные `pytest` и `uv sync` не запускают генерацию.

## Границы результата

Текст ответа проверен вручную относительно **одного** passage: утверждение о 300 dpi
поддержано источником. Это не независимая оценка качества; receipt остаётся
`REQUIRES_REVIEW`. Нет проверки prompt-injection устойчивости реальной модели,
разнообразных вопросов, русского языка, dense+LLM, multi-user нагрузки или SLO.
Температура 0.7; существующий общий client не передаёт seed: повторяемость идентичного
текста не заявляется. Memory peak и денежная стоимость не измерялись.

Пять [учебных пробелов](wave2-coverage.md#coverage-gaps-20261028) — отдельная линия;
после этого опыта для них [подготовлены материалы](five-gaps-verification.md).
Сам generator experience их не закрывает. vLLM **DEFERRED_ENV** до Linux/WSL.
Learner TODO, отчёты, progress, CLI и существующие ID не изменены.

## Технические проверки

Из корня, `.venv-base-check/Scripts/python.exe`:

- `-m pytest -q`: **1393 passed, 78 skipped, 1162 xfailed**, 125.77 s;
  один существующий Starlette/AnyIO deprecation warning. xfail не зачтены ученику.
- `-m pytest labs/03_real_rag/test_local_generator.py -q`: **15 passed**, 1.06 s;
  network guard активен, transport fake только на HTTP boundary.
- `-m ruff check .`: PASS; `-m ruff format --check .`: **993 files** PASS.
- `-m mypy`: **686 files** PASS; `-m mypy -p labs.03_real_rag.local_generator -p labs.03_real_rag.test_local_generator`:
  **2 files** PASS.
- `-m pytest labs/03_real_rag labs/05_model_serving tests/integration/test_markdown_links.py -q`:
  **115 passed, 8 skipped**, 3.51 s.
- Дополнительная проверка шести затронутых Markdown documents, включая новые
  untracked: **353 local links / 28 anchors**, проблем нет. Это проверка ссылок,
  визуальное отображение в редакторе отдельно не проверялось.
- `git diff --check`: PASS; HEAD остаётся `836028944eceaa260cb47d0056b593af4a4648d4`.

Hash-сверка с сохранённой полной картой 1043 файлов до подготовки дизайна:
из старых файлов изменены только `docs/roadmap.md`, `docs/wave2-coverage.md` и
входной `labs/03_real_rag/README.md`. Добавлены spec, plan, этот отчёт, adapter и tests.
Существующие Python-реализации, student/report/progress и зависимости совпадают по SHA256.

Полный pytest проверяет разработческую целостность. Ученическое понимание и
строгий `check` остаются отдельными: ни одного учебного TODO здесь не решено.

Свежий независимый code review: actionable findings **0** в ограниченном scope адаптера,
tests и документации. Reviewer не повторял runtime/tests; поздние hash/provider-error
свидетельства перепроверены основным исполнителем. Это не независимый ML evaluation.
Оставлены границы доверенного локального teacher-опыта: защита от скомпрометированного
daemon, конкурентной смены tag и враждебных файловых гонок не заявляется.
