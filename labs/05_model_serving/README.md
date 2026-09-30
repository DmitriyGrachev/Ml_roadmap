# Model serving и vLLM — спецификация

CORE concepts; vLLM OPTIONAL · PLANNED. Реального serving benchmark пока нет.

Prerequisites: [backend](../../modules/02_python_backend/README.md),
[HF inference](../02_huggingface_models/README.md), [production](../../modules/08_production_ai/README.md).
Fine-tuning исходной модели не prerequisite.

Expected artifacts: отдельное совместимое Linux/WSL serving environment/lock,
один model API или batch process, FastAPI client, limits и bounded load script,
измеренный report модели/config/input lengths/output caps/concurrency/cold-warm.

Разделить CPU/GPU inference, batch и LLM serving. Изучить weights/activation/KV
memory, dtype/quantization/batching, prefill/decode; Ollama можно выбрать для
первого локального старта, vLLM — отдельный опыт без training dependencies.

Done: измерены TTFT, token rate, end-to-end latency, throughput, ошибки и память;
есть streaming/cancellation/deadlines/backpressure/queues/bounded retries.
Маленький smoke не репрезентативный benchmark. CUDA, Windows/vLLM и конкретная
модель в 8 GB требуют реального подтверждения, а не инструкции в README.
