# Почему генератору нужен serving

После [backend](../../modules/02_python_backend/README.md),
[локального inference](../02_huggingface_models/README.md) и
[production contracts](../../modules/08_production_ai/README.md) задача меняется:
модель должна отвечать нескольким клиентам, укладываться в память и прекращать
ненужную работу. Результат урока — объяснить задержку, выбрать ограниченную нагрузку
и честно прочитать измерение. До запуска прочитайте [Linux маршрут](environment/README.md).
Реальный vLLM обязателен; этот текст и synthetic tests его не заменяют.

## Сначала прогноз

Два клиента отправляют одинаковые короткие вопросы. Один видит ответ сразу,
второй ждёт секунду до первого слова. Модель одна и та же. Может ли это быть
очередь, а не ухудшение качества? Что изменится, если оба попросят длинный ответ?

CPU inference означает вычисление на CPU; GPU inference — вычисление на GPU.
Оба могут быть одиночным вызовом без HTTP. Batch inference объединяет примеры
для вычислений; serving добавляет приём запросов, планирование, очереди,
отмену, лимиты и доставку результата. HTTP wrapper над одиночным `generate`
ещё не обеспечивает хорошее планирование нескольких генераций.

```text
Windows client / Linux client
          | HTTP, только loopback
          v
  admission: принять или отказать
          | ограниченная очередь
          v
 Linux vLLM runtime -> CUDA/PyTorch -> NVIDIA GPU
          | prefill -> decode -> decode -> ...
          +------------ SSE answer chunks ----------> client
```

В WSL Linux runtime использует GPU через Windows driver. Нативный Linux работает
без Windows host. Драйвер даёт доступ к устройству, CUDA runtime и скомпилированные
kernels выполняют операции, Python вызывает их. Наличие GPU в `nvidia-smi`
не означает, что CPU wheel PyTorch умеет CUDA. Сейчас training PyTorch — CPU,
GPU в Linux не проверен: **NOT_RUN**. Отдельный serving lock не меняет training lock.

## Prefill, decode и формы

Пусть tokenizer после chat template дал вход `input_ids` формы `[B, T] = [1, 4]`:
одна последовательность из четырёх токенов. IDs — целые числа, а не векторы слов.
Embedding превращает их в `[1, 4, D]`, где `D` — hidden dimension. Во время
prefill модель обрабатывает вход, создаёт KV cache и logits для следующего токена.
В обычном autoregressive decode следующий токен зависит от уже выбранных;
последующие шаги добавляют по одному токену. Это учебная схема без speculative decoding.

```text
prefill: [a b c d] -> next token e; cache содержит позиции a..d
decode:          [e] -> next token f; cache содержит a..e
decode:          [f] -> next token g; cache содержит a..f
```

В attention для одного слоя K и V можно мыслить как два массива
`[B, Hkv, T, Dh]`. `Hkv` — число KV heads, `Dh` — размер одного head;
query heads при grouped-query attention могут быть многочисленнее KV heads.
Реальная память vLLM разбита на блоки и может иметь другую физическую раскладку.
Длинный prompt нагружает prefill и cache, длинный output добавляет decode шаги.
Сокращение prompt может ухудшить ответ: число токенов — ресурсный лимит, не качество.

Прогноз: если выход пока неизвестен, можно ли получить все будущие токены
одним обычным decode шагом? Нет: следующий шаг использует выбранный предыдущий токен.
Чанки HTTP при этом могут объединять несколько токенов или частей текста.

## Память: веса не равны всему процессу

```text
VRAM процесса (схематично, ширины не пропорциональны)
| weights | KV pool | activations/workspaces | graphs/runtime |
  фиксированы     зависят от длины/числа запросов/плана runtime
VRAM устройства также занята экраном и другими процессами.
```

Для условного ровно `P = 1_000_000_000` параметров FP16:
`P × 2 bytes = 2_000_000_000 bytes = 2 GB ≈ 1.86 GiB` только весов.
GB — `10^9` bytes, GiB — `2^30` bytes, MiB — `2^20` bytes. Это не размер всех
файлов snapshot и не peak VRAM. У настоящей модели точное число параметров и
сохранённый dtype могут отличаться от округлённого имени «0.6B».

Для идеализированного одинакового cache во всех слоях:

```text
KV bytes = 2 × L × B × Hkv × T × Dh × s
           ^ K и V                    ^ bytes на элемент
```

Здесь `L` — слои, `B` — активные последовательности одинаковой длины,
`T` — сохранённые позиции в каждой, `s` — bytes одного элемента.
Tiny пример: `L=2, B=1, Hkv=1, T=4, Dh=8, s=2`.
Один K занимает `1×1×4×8×2 = 64 bytes`; K+V — 128 bytes на слой;
два слоя — **256 bytes**. При `T=8` получится 512 bytes, при дополнительном
`B=2` — 1024 bytes. Веса от этих изменений не удваиваются.
Это арифметика массивов, не показания GPU. Cache pool vLLM может быть
зарезервирован заранее; `nvidia-smi` тогда не повторяет эту линейную зависимость.
Видимый расход процесса и полезные занятые cache blocks — разные показатели.

FP32 использует 4 bytes, FP16/BF16 обычно 2; диапазон чисел и точность различаются.
Quantization меняет представление значений, добавляет scales/metadata и требует
совместимых kernels. INT4 не означает ровно «вся память в четыре раза меньше»:
activations и KV могут остаться в другом dtype. Уменьшение контекста сокращает
сохранённые позиции, quantization весов меняет другой компонент. Первую проверку
делаем FP16, eager, context 1024, one sequence; это кандидат профиля, не обещание fit.

## Очередь и batching

Статический batch ждёт группу и обрабатывает её вместе. Continuous batching
позволяет планировщику добавлять новые запросы по мере завершения старых.
Это может поднять общий throughput, но не обязано уменьшать задержку каждого клиента.
`max-num-seqs=1` ограничивает число одновременно планируемых последовательностей,
а не бесконечную очередь входящих HTTP запросов. Нужен отдельный admission limit.

Разобранный игрушечный план без реального GPU: один worker, очередь максимум один.
A приходит в 0 ms и работает до 40 ms; B приходит в 10 ms и ждёт;
C приходит в 20 ms и получает отказ — очередь уже полна. Если B имеет deadline
30 ms от собственного прихода, он истекает в 40 ms: его не следует начинать
после истечения, даже если worker только что освободился. Политика равенства
`now >= deadline` должна быть явной.

Ошибка — создать задачу на каждый вход и спрятать все за semaphore: active count
ограничен, но ожидающих задач может быть сколько угодно. Teacher batch конечен:
не более восьми запросов и concurrency 1 или 2. Это bounded load generator,
а не production gateway с реализацией HTTP admission. Самостоятельный перенос —
в [вариации](variation.md), без готового student service.

## Streaming: HTTP bytes, SSE records и токены

Server-Sent Events (SSE) отделяет события пустой строкой. Поля `data:` могут
занимать несколько строк; comment/heartbeat начинается `:`. Сетевой read может
закончиться посередине JSON или многобайтной UTF-8 буквы. Поэтому клиент сначала
собирает полные записи и только затем декодирует и читает JSON.

[Teacher client](demo_client.py) принимает OpenAI-compatible chat stream:
role/usage/reasoning metadata не считаются первым текстом ответа, непустой
`delta.content` считается; `[DONE]` завершает stream. EOF без `[DONE]`, неверный
JSON/type, HTTP error или provider error дают явный неуспех с сохранённым partial
text в памяти. В отчёте текст и prompt не сохраняются. Размер записи/ответа ограничен.
Ни import, ни pytest не обращаются к реальному endpoint.

Пример из synthetic transport теста, **не benchmark**:

```text
dispatch   role       answer 1   answer 2    usage       DONE
 0 ms      100 ms      300 ms     400 ms      500 ms      600 ms
 |---------- TTFT 300 ms --------|
 |---------------- E2E 600 ms ----------------------------|
 content delta: 400 - 300 = 100 ms (между чанками, не токенами)
 usage: prompt_tokens=9, completion_tokens=3; answer content chunks=2
```

Код → состояния: первая запись меняет role, но `offsets=()`; непустой текст
добавляет `300`; следующий текст добавляет `400`; usage сохраняет числа `9,3`;
DONE завершает чтение и закрывает response. Итог теста: `status=ok`, текст
`Привет!`, `ttft_ms=300`, `e2e_ms=600`, `content_deltas_ms=(100,)`.
Изменённая строка: первая content строка пустая — она не начинает TTFT;
первый непустой текст теперь в 400 ms. Проверить соседним самостоятельным fixture.

TTFT (time to first token) здесь операционно означает **первый непустой answer
content на клиенте**. Серверный первый сгенерированный токен может быть раньше,
особенно при thinking. E2E начинается при dispatch до подключения и включает
server queue/prefill/decode/доставку; локальная queue учитывается отдельным `queue_ms`.
Для admitted запроса полное клиентское время ≈ `queue_ms + e2e_ms`.
Для истёкшего до admission: `queue_ms > 0, e2e_ms=0, ttft_ms=null`.

В приведённом synthetic примере `3 / 0.6 = 5 output tokens/s` — throughput
успешного запроса за его полное E2E, **не decode token rate**. Чтобы оценить decode
rate `(Nout-1)/(t_last_token-t_first_token)`, нужны реальные времена токенов;
чанковая шкала их не даёт. Если tokenizer/server usage недоступны, token rate
остаётся unknown. В batch denominator — wall time всего опыта, а не сумма
перекрывающихся E2E. Сравнивать только одинаковую definition и cold/warm условия.

## Deadline, cancellation и ошибки

Read timeout ограничивает ожидание отдельной операции; сервер может присылать
heartbeat каждые 5 s бесконечно. Total deadline ограничивает весь запрос,
в teacher batch включая локальное ожидание места. `asyncio.timeout` использует
monotonic clock; системная корректировка календарного времени не сдвигает бюджет.

Caller cancellation прерывает ожидание и закрывает connection. Это свидетельство
клиента, а не доказательство освобождения server KV: после реального опыта проверить
server logs/метрики и возможность следующего запроса. Клиент делает ровно одну
попытку, **ноль automatic retries**, включая connect errors. После partial answer
повтор может дублировать вывод и работу; retry policy не заменяет admission control.
Новый операторский запуск после диагностики — отдельный опыт, не скрытый replay.

При OOM/недостатке KV остановить опыт, сохранить конфигурацию и показания, убрать
ненужные процессы, выбрать меньший бюджет или модель. Не увеличивать memory
utilization вслепую. Deadline/503/malformed и OOM нельзя записывать как «быстрый ответ».

## Проверка понимания

1. Почему `nvidia-smi` работает, а `torch.cuda.is_available()` в training — false?
2. Для tiny KV примера что изменится при удвоении `Hkv`, но неизменном `P`?
3. Почему два content chunks и три completion tokens не противоречат друг другу?
4. Какой TTFT запишется, если в 100 ms пришёл role, в 200 ms reasoning,
   а в 800 ms первый непустой answer content?
5. Почему concurrency 2 может увеличить throughput и ухудшить отдельный E2E?
6. Какие два независимых свидетельства нужны, чтобы заявить, что cancellation
   освободил работу на сервере? Почему client close недостаточно?
7. Почему успешный `/v1/models` и synthetic tests не доказывают реальный vLLM,
   воспроизводимый restart и качество русского ответа?

После ответов выполните [независимую вариацию](variation.md). Для переноса полезны
существующие
[`backend-provider-fanout`](../../modules/02_python_backend/05_async_endpoints/exercises/provider_fanout/README.md)
и [`production-request-metrics`](../../modules/08_production_ai/exercises/request_metrics/README.md)
как prerequisites; их TODO
не решаются этим примером. Полный перенос в сервис/RAG выполняется отдельно.

## Источники и границы

Проверено чтением официальных страниц 11.10.2026; команды Linux ещё **NOT_RUN**.
Англоязычные материалы: [vLLM GPU installation](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/)
— только Requirements и fresh environment/kernels;
[serve reference](https://docs.vllm.ai/en/latest/cli/serve/)
— dtype/context/sequences/eager/memory и соответствующие флаги;
[Qwen3 model card](https://huggingface.co/Qwen/Qwen3-0.6B)
— switching thinking/non-thinking. Остановиться до provider/cloud примеров.
Граница текущего результата: транспортные механизмы проверены offline,
Linux/CUDA/vLLM/качество/benchmark остаются NOT_RUN; понимание — REQUIRES_REVIEW.
