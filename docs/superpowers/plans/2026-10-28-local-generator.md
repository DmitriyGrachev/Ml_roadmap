# Бounded local generator implementation

Goal: измерить первый реальный ответ существующей Ollama/Qwen без downloads.
Architecture: lexical retrieval/ACL → существующий bounded SSE client → строгий Draft.
Tech stack: Python 3.12, существующие httpx/pytest, установленная Ollama.
Spec: [согласованный дизайн](../specs/2026-10-28-local-generator-design.md).

## Global constraints

Работать в текущей dirty feature branch; не менять student/progress/ID/contracts.
Никаких Git mutations, downloads, installs, публичных endpoints. Один запуск runtime;
при необходимости серьёзной настройки перейти к первому из пяти пробелов.
Никакого зачёта качества по одному smoke. vLLM DEFERRED_ENV.

## Task 1 — адаптер

Interfaces: старый sync Generator/Draft, новый async generate, serving.stream_chat.
Сначала offline tests на корректный JSON/citations, partial/truncated/provider errors,
ACL/no evidence и active loop; увидеть RED из-за отсутствия реализации.
Затем минимальный адаптер и явный CLI с fresh output, без изменения dense/coupled.
Expected: focused tests green; CLI без явного consent не обращается к runtime.

## Task 2 — реальный опыт и отчёт

Проверить SHA всех cached blobs; loopback-only existing runtime; bounded API call.
Сохранить identity/config/prompt/context/output/TTFT/E2E, неизвестное как null.
Expected: реальный результат или честный отказ и переход к gap 1.
Проверить полный pytest, Ruff/format, mypy, links, сохранность baseline.
Независимый финальный review. Commit/push запрещены.

## Review focus

1. Утечка staff/context через prompt или artifacts.
2. False success при partial/length/ошибках/citation mismatch.
3. Скрытая сеть/download/proxy/retry или overwrite.
4. Смешение runtime PASS, grounding и ученического зачёта.
5. Изменение существующего dirty кода и зависимостей.
