# 03. Что видно при эксплуатации

Практический вопрос: восемь обращений к G-01 завершились разными способами. Если лишь три дали технически успешный ответ и нет ни одной live-метки качества, что мы вправе сообщить? Перед запуском [teacher walkthrough](../walkthrough.py) предскажите p95 по временам `10, 20, 10, 10, 10, 30, 20, 20` ms. Это *авторские simulated milliseconds из A*, а не замер provider или сервиса.

**Интуиция.** В backend-сервисе **logs** отвечают «что случилось», **metrics** — «сколько за окно», **traces** — «какой путь прошёл конкретный запрос». У модели есть дополнительный вопрос о правильности содержания, и без reference label или human feedback он остаётся открытым. `run_id` и release ID помогают соединять минимальный event с соответствующим trace и версией. Высококардинальный `run_id` не должен становиться label каждой metric series. [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/) описывают эти виды сигналов; наш JSON не является инструментированной OpenTelemetry-трассой.

**Исходное фиксированное окно.** Все восемь строк производятся из `build_demo()` Module 07; `tool_attempt_events` считается по trace event `tool_attempt`, proposal — по `proposal`, а реальные model calls равны нулю. Никакие checkpoint, approval digest, аргументы reminder или текст запроса в выдачу B не копируются.

| run_id | outcome A | simulated latency, ms | tool attempts | authored proposals |
| --- | --- | ---: | ---: | ---: |
| answer | answered | 10 | 0 | 0 |
| success | reminder_recorded | 20 | 1 | 1 |
| denied | permission_denied | 10 | 0 | 1 |
| refused | refuse | 10 | 0 | 1 |
| cancelled | cancel | 10 | 0 | 1 |
| failure_recovered | reminder_recorded | 30 | 2 | 1 |
| attempt_exhausted | attempt_limit | 20 | 1 | 1 |
| unknown_after_effect | unknown_needs_reconciliation | 20 | 1 | 1 |

**Ручной расчёт.** Окно — ровно перечисленные восемь кейсов, а не «последние сутки». Technical successes = `answer`, `success`, `failure_recovered`: `3/8`. Technical errors по *принятой для этой учебной таблицы классификации* = `attempt_exhausted` и `unknown_after_effect`: `2/8`. Cancellation = `1/8`, refusal = `1/8`, permission denial = `1/8`; эти категории вынесены отдельно и не исчезают из общего знаменателя. Если другой продукт включает denial в error SLI, числитель надо объявить заново. Отсортированные **все** времена, включая ошибки и отмену: `10,10,10,10,20,20,20,30`. Nearest-rank p95 берёт позицию `ceil(0.95×8)=8`, значит `30 ms`; усреднение p95 по маршрутам не даёт общего p95. Сумма tool attempts `0+1+0+0+0+2+1+1=5`, scripted proposal events `7`, real model calls `0`. Условная ставка `2 simulated credits` за attempt даёт `10/16` из учебного budget и остаток `6`. Эти credits не являются ценами провайдера или фактом списания.

`live_quality_labels_received=0`, значит quality denominator `0` и rate `null/unknown`, а не `0%` ошибок или `100%` правильности. Четыре reference labels из локального [release comparison](../02_releases_evaluation/theory.md) относятся к **другой**, авторской offline-таблице и не подменяют отсутствующую обратную связь этого окна. В реальности label может прийти позже и только от части пользователей; нужно соединять его с исходным request/release и показывать coverage/задержку.

Точный механизм: собирайте event с ограниченными outcome codes и release ID; агрегируйте по явно указанному временному окну и eligible population; храните raw latency для глобального percentile; trace оставляйте для разбора ветви конкретного run. Sampling logs/traces или потеря cancellation events меняют видимую популяцию. Пять-восемь учебных событий — не benchmark, SLO и не доказательство uptime. Самостоятельная вариация: исчезли метки только у запросов с отказом. Какие два знаменателя и какую задержку обратной связи покажете до вывода о качестве? [Request metrics](../exercises/request_metrics/README.md), ID `production-request-metrics`, оставляет общий алгоритм по route ученику; [error budget](../exercises/error_budget/README.md), ID `production-error-budget`, требует свою политику полного окна. См. [LLM evaluation](../../05_llm_engineering/05_evaluation/theory.md).

Источники: OpenTelemetry, [Signals](https://opentelemetry.io/docs/concepts/signals/), англ., различие logs/metrics/traces; Google SRE, [Implementing SLOs](https://sre.google/workbook/implementing-slos/), англ., выбор события и знаменателя; Google ML Crash Course, [Monitoring pipelines](https://developers.google.com/machine-learning/crash-course/production-ml-systems/monitoring), англ., мониторинг данных и качества.
