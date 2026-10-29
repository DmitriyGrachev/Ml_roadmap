# Model serving и обязательный vLLM

**CORE · PLANNED: vLLM обязателен** по уточнению пользователя от 11 октября 2026.
Реальный запуск и serving benchmark пока **NOT_RUN**. Авторские offline материалы
подготовлены; это не готовый зачёт и не проверка Linux/GPU совместимости.
Фактический vLLM этап **DEFERRED_ENV** по решению пользователя 11.10.2026:
на текущем ноутбуке нет Linux/WSL. Продолжить после подготовки подходящего host.

Маршрут: [теория с разобранными примерами](theory.md) →
[Linux environment и inventory](environment/README.md) →
[явный endpoint smoke](smoke/README.md) →
[измерения и пустой шаблон отчёта](experiments/README.md) →
[самостоятельная вариация и защита](variation.md).

Teacher [streaming client](demo_client.py) работает с уже подготовленным loopback
endpoint и явным server model id. Ничего не устанавливает/скачивает при import.
Обычный pytest использует только помеченные synthetic transports:

```powershell
.venv/Scripts/python.exe -m pytest labs/05_model_serving -q
.venv/Scripts/python.exe -m labs.05_model_serving.environment.preflight labs/05_model_serving/environment/manifest.template.json
```

Вторая команда на нынешней Windows завершается exit 2 / NOT_RUN до импорта GPU
runtime. Это ожидаемый отказ, не установка. Реальный endpoint автоматически не вызывается.

Место реализации: [пакет R08 единого плана](../../docs/superpowers/plans/2026-10-11-remaining-roadmap.md#r08).
После стартового Qwen3-0.6B подготовлены [ещё два кандидата](../../docs/compute-guide.md#vllm-candidates);
выбирать по одному, не считать их проверенными на RTX 5060 и не скачивать автоматически.

Prerequisites: [backend](../../modules/02_python_backend/README.md),
[HF inference](../02_huggingface_models/README.md), [production](../../modules/08_production_ai/README.md).
Fine-tuning исходной модели не prerequisite.

Место: обязательный результат после этапа 4 основного плана и указанных prerequisites,
перед необязательными специализациями. Вводный CPU API этапа 3 не заменяет эту lab.

## Среда

Основной предложенный маршрут — Ubuntu 24.04 LTS в WSL2 с RTX 5060 Laptop 8 GB.
Сервер запускается в Linux, а не в нативном Windows Python; клиент может остаться
в Windows. Если требуется полностью исключить Windows host, использовать отдельную
Linux машину с NVIDIA GPU, собственную или удалённую. Аренда — только после
согласования бюджета. [Профиль, ограничения и стартовые параметры](../../docs/compute-guide.md#vllm-linux-route).

Отдельная serving среда и её lock не изменяют базовую или training среду проекта.
Загрузки модели, установка WSL и запуск внешнего сервера — явные отдельные действия.
Первый API слушает только loopback; удалённый доступ не требует публичного порта.

## Небольшие последовательные результаты

1. Проверить GPU из Linux, согласованность версий и маленький CUDA расчёт.
2. Явно получить разрешённую небольшую модель фиксированной revision, затем
   поднять vLLM с локальным snapshot. Проверить readiness и обычный API ответ.
3. Подключить FastAPI/Python клиент, проверить streaming и ограничение длины,
   timeout/cancellation; состояние очереди не должно расти без ограничений.
4. Сравнить короткие запросы при concurrency 1 и 2, если позволяет память;
   записать ошибки и ограничения, остановить сервер и воспроизвести запуск.
   Если второй режим невозможен, сохранить причину и безопасное отклонение
   перегрузки — ускорение не обязано появиться.

Expected artifacts: отдельное совместимое Linux environment/lock, версии
драйвера/CUDA/PyTorch/vLLM, model/tokenizer revision, команда запуска с лимитами,
vLLM API и клиент, bounded load script, исходные measurements и отчёт с input
lengths/output caps/concurrency/cold-warm. Секреты и модельные веса в репозиторий
не включаются. Окружение/модель выбираются с учётом памяти, а не по размеру модели
из чужой демонстрации.

Разделить CPU/GPU inference, batch и LLM serving. Изучить weights/activation/KV
memory, dtype/quantization/batching, prefill/decode. Для каждого механизма нужны
русское объяснение, маленький разобранный пример и самостоятельная вариация.
Визуальные опоры: клиент → очередь → prefill/decode → streaming; weights/KV cache;
шкала первого и последующих токенов. Графики строить из измерений, не вымышленных чисел.
Ollama/HF inference допустимы для сравнения, но не закрывают обязательный vLLM опыт.

Критерий Done, **пока не достигнут**: выполнен реальный Linux/vLLM запуск и перезапуск;
измерены TTFT, token rate, end-to-end latency, throughput, ошибки и память;
есть streaming/cancellation/deadlines/backpressure/queues/bounded retries.
Маленький smoke не репрезентативный benchmark и не ML evaluation. Совместимость
CUDA/Blackwell/WSL и конкретная модель в 8 GB требуют реального подтверждения,
а не инструкции в README. При локальном ограничении меняется Linux среда или
модель, а не обязательность vLLM. Формальная самостоятельная сдача теперь зарегистрирована как
[`lab-vllm-measurements`](assessment/README.md): learner arithmetic, сохранённые
измерения и evidence bundle. Обязательные missing/NOT_RUN не дают строгий зачёт.
Вариация и происхождение runtime оцениваются человеком: **REQUIRES_REVIEW**.
Ученический отчёт остаётся пустым.
