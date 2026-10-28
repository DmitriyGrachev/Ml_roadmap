# Первый локальный генератор: Windows + существующая Ollama

Статус: runtime, модель и границы дизайна согласованы пользователем 28.10.2026.
При неудаче без серьёзной перенастройки перейти к пяти учебным пробелам. Это продолжение
существующего R07, не замена vLLM и не выполнение ученических заданий.

## Цель, варианты и границы

Получить первый измеренный LLM-ответ по разрешённому контексту существующей
[RAG lab](../../../labs/03_real_rag/README.md), сохранить ошибки и ограничения.
Выбран существующий Ollama + `qwen2.5:latest`: не нужны новые downloads/runtime.
Альтернатива llama.cpp потребовала бы отдельной установки и настройки; vLLM/SGLang
относятся к последующему Linux production-serving опыту, сейчас он отложен.

Preflight: Ollama 0.40.11 установлен, server не запущен; Qwen2.5 7.6B Q4_K_M
manifest и заявленные blob sizes присутствуют. Manifest SHA256
`156bcbf71df68f7a6581fb4ab306ed921b8114d82b6eaeab5c0442785ea9b4c3`.
Все blob SHA256 ещё не проверены. Tag `latest` сам по себе не immutable identity:
перед запуском проверить bytes и выбранный server digest, сохранить их в receipt.
Фактически обнаружена RTX 5060 Laptop, total8151 MiB; вместимость и скорость
этой конфигурации не объявляются проверенными до реального опыта.

## Минимальная реализация

- Добавить небольшой адаптер в `labs/03_real_rag/local_generator.py` и его tests;
  переиспользовать `labs.05_model_serving.demo_client.stream_chat`, `ClientConfig`,
  bounded SSE parser и установленный HTTP client. Новый SDK/фреймворк не нужен.
- Сохранить старый synchronous `Generator`/`Draft` и `answer_query`; отдельный
  CLI adapter не вызывается из уже работающего event loop. Не превращать lab в
  новый web server и не менять старые provider/student contracts.
- В первом пакете использовать существующий lexical retrieval и
  `assemble_context`: ACL до top-k, затем current revision/digest/text/access
  перед единственным provider call. Доверенный actor access не брать из request.
  Передавать только отобранные public passages, не весь teacher corpus.
- Вызывать только явный HTTP loopback `/v1`, без облака/proxy/redirects,
  без автоматических pull/fallback/retries. Сохранить deadline/output/byte limits.
  Проверить совместимость фактической Ollama с request fields клиента; изменение
  общего клиента допускается только минимальное и с regression tests.
- При timeout/partial/truncation/невалидном ответе не выдавать успешный Draft.
  Citation IDs извлекать из ответа и валидировать; не приписывать автоматически
  все переданные источники. Синтаксическая валидность не доказывает support claims.
- Явный CLI smoke и новый ignored output: версия runtime, model digest/config,
  prompts/context identities, ответы/citations/status, token counts при наличии,
  реальные TTFT/E2E и ограничения. Student report не заполнять; answer quality
  остаётся REQUIRES_REVIEW, неизвестные memory/cost — null с причиной.

Это согласованное внутреннее устройство; результаты требуют фактической проверки.
Согласованный baseline
MiniLM/Qdrant не перезаписывать. Его отдельное подключение к генератору потребует
нового согласованного опыта; mutation `qdrant_smoke` index для этого непригоден.
Lexical + LLM первый опыт не закрывает полный R07/Document Intelligence.

## Проверка и неизменяемые части

Unit tests без сети: valid/invalid citations и JSON, пустой/отозванный контекст без
provider call, timeout/partial/truncation, отсутствие скрытых загрузок и overwrite.
Explicit smoke: настоящий выбранный локальный runtime и synthetic public corpus,
включая ответимый/нет оснований/provider error; не применять порог, подобранный по
этим же случаям. Проверить фактические ответы отдельно от инфраструктурного PASS.
Ruff/format/mypy и relevant regression, затем соразмерный полный regression suite.

Не менять TODO, learner implementations/reports/progress, curriculum ID/CLI и
смысл test/check. Не устанавливать WSL/Docker, не скачивать модели/датасеты,
не публиковать endpoint и не делать commit/push/merge. vLLM DEFERRED_ENV.
Пять пробелов объяснения/практики сохраняются отдельным
[PLANNED продолжением](../../wave2-coverage.md#coverage-gaps-20261028), а не исчезают
после первого generator run.
