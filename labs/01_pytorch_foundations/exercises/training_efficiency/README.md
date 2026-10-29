# Эффективность обучения и logical batch

**lab-training-efficiency · обязательная CPU механика, opt-in GPU практика.**
Prerequisites: [PyTorch foundations](../../README.md), backward, mean loss, optimizer
state и отличие train/eval. Ученик реализует только `starter.accumulated_step`;
готового универсального решения в author примере нет.

## Сначала посчитайте веса

Пусть logical batch содержит 6 строк, micro-batches — 3, 1 и 2 строки. Mean losses
каждого micro-batch взвешиваются как `3/6`, `1/6`, `2/6`. Тогда gradient совпадает
с mean loss полного batch. Деление каждого loss на 3 неверно: одиночная строка
получит в три раза больший вес, чем строка первого micro-batch.

`loss_fn` возвращает скаляр, усреднённый **по строкам**, при одинаковой структуре
строки. Для token loss с разным числом валидных tokens нужен вес по числу targets,
а не по строкам; это другой контракт. Данная задача не решает его автоматически.
Не выполняйте optimizer.step для каждого micro-batch: Adam moments, momentum и
weight decay тогда изменяют траекторию. Очистите старые gradients один раз перед
logical batch, backward накопит вклады, затем сделайте ровно один step. Верните
row-weighted scalar loss. Empty input и empty micro-batch — ValueError до update.
Caller владеет train/eval и optimizer; функция не пересоздаёт их и не меняет mode.

```bash
uv sync --python 3.12 --group training
.venv/bin/python -m pytest labs/01_pytorch_foundations/exercises/training_efficiency/test_starter.py -q
```

Windows: `Scripts/python.exe` вместо `bin/python`. Tests используют deterministic
CPU Linear, float64, SGD momentum и сравнивают loss, gradients, параметры и state
с полным batch два update подряд. Они ловят stale gradients, uneven last batch и
лишние optimizer steps. TODO отмечается xfail; строгий check требует реализацию.
Author `test_gpu_contract.py` не входит в learner completion.

## Batch, steps и память

| Термин | Значение и ловушка |
| --- | --- |
| micro-batch | одна forward/backward порция; обычно определяет peak activations |
| optimizer step | обновление параметров и optimizer state после накопления |
| effective batch | сумма строк всех micro-batches; при DDP также всех ranks |
| epoch | проход по train rows; drop_last может молча удалить остаток |
| AMP | часть операций в меньшей precision; scaling помогает fp16 gradients |
| activation checkpointing | recompute forward при backward ради меньшей памяти |
| optimizer state | например moments Adam; память есть даже при малом batch |

Для равных micro-batches привычная формула — batch × accumulation × world_size.
Для неравного последнего logical batch считайте реальные rows. Accumulation не
сокращает память weights или optimizer states. AMP не просто `model.half()`:
autocast выбирает dtype операций, GradScaler обрабатывает underflow и может
пропускать update при overflow. Тогда число запрошенных и выполненных steps может
отличаться. Checkpointing увеличивает вычисления, требует внимания к stochastic
операциям/RNG и side effects. Эквивалентность full batch ограничена: dropout,
BatchNorm batch statistics и floating point порядок могут менять результаты.
Поэтому CPU контракт использует deterministic Linear без batch-dependent слоёв.

## Явный GPU experiment

Default repository torch — **CPU**. Используйте отдельно подготовленное совместимое
CUDA окружение; этот runner ничего не устанавливает и не скачивает.

```bash
.venv-cuda/bin/python -m labs.01_pytorch_foundations.exercises.training_efficiency.gpu_runner --output artifacts/gpu-fp32-01 --steps 5
.venv-cuda/bin/python -m labs.01_pytorch_foundations.exercises.training_efficiency.gpu_runner --output artifacts/gpu-amp-01 --steps 5 --amp
.venv-cuda/bin/python -m labs.01_pytorch_foundations.exercises.training_efficiency.gpu_runner --output artifacts/gpu-checkpoint-01 --steps 5 --checkpoint
```

Новый каталог на каждый run; pytest/import не запускает GPU. Synthetic model имеет
256→512→16, batch 32 и 1 warmup + ≤20 measured steps. Warmup создаёт optimizer
state до замера. `synchronize()` перед/после участка отделяет CUDA asynchronous
work от CPU enqueue time; `reset_peak_memory_stats()` сбрасывает peak счётчики.
Report содержит фактически измеренные seconds/step, baseline/peak allocated и
peak reserved bytes, device/version, flags и losses. Allocated — занятая tensors
память allocator; reserved — pool, не равный живым tensors. Это не полная память
процесса/драйвера и не обещание размера доступной LLM. На таком маленьком model
AMP/checkpointing могут быть медленнее: измерьте, не предполагайте выигрыш.

При отсутствии CUDA — RuntimeError с **NOT_RUN**, успешный report не создаётся.
В этом curriculum GPU результаты **NOT_RUN**, CPU тесты не означают CUDA успех.
[QLoRA recipe](../../../04_llm_finetuning/sft_workflow/README.md#opt-in-qlora)
добавляет 4-bit base, но adapters, activations и optimizer всё равно занимают память;
8 GB VRAM не гарантируют конкретный размер модели.

## Критерии переноса

Объясните вес последнего micro-batch и разницу rows/tokens. Покажите совпадение
полного logical update и накопления, включая momentum. Для реального workload
зафиксируйте seed, sequence length, micro/effective batch, dtype, optimizer,
число update, warmup и measurement region; сравнивайте одинаковую работу.
Решение об AMP/checkpointing принимайте по своим измерениям и качеству, а не по
synthetic benchmark или чужой hardware таблице. Не приписывайте CPU run GPU metrics.
