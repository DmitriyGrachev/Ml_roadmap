# PA1: журнал проверки прикладных инструментов

Дата: 29 октября 2026. Ветка: `namepfchekcoutbranch-extended-pa1`.
Основание: опубликованный `codex/ml-engineer-readiness`, commit
`2c75f94becc999975cc397bbf4013716b46d4568`.

Это журнал исправности новых материалов, а не отчёт об освоении их учеником.
Исходная база уже прошла [Ubuntu/Windows CI](https://github.com/DmitriyGrachev/Ml_roadmap/actions/runs/40793287000).
Повторный baseline и полный локальный suite для этой ветки не запускались.
Предобученные веса и внешние датасеты не скачивались; GPU training и серверы
не запускались. Для проверки API создавались маленькие локальные случайные модели.

## Состав и среда

Добавлены 11 catalog ID, исходные 180 записей сохраняются. Новые checkpoints,
MLflow stores и learner reports создаются в отдельных ignored directories,
а не публикуются как готовые ответы. Порядок изучения находится в
[карте практики](applied-tools-practice.md).

Optional CPU environment установлен один раз из нового lock: torch 2.14.0+cpu,
Transformers 5.17.0, Datasets 5.0.1, Accelerate 1.15.0, PEFT 0.21.2,
TRL 1.16.0, Sentence Transformers 6.2.0, MLflow 3.17.0, Optuna 5.0.0.
Метаданные bitsandbytes 0.50.2 входят в отдельную группу `quantization`, но пакет
не устанавливался в CPU environment и CUDA-совместимость не проверялась.

## Короткие проверки до интеграции

| Область | Что реально проверялось | Результат локального среза |
|---|---|---|
| NumPy/Pandas/sklearn | Три фиксированных author examples, learner edge-case contracts; мутации масок, границы времени и holdout fit ловятся тестами | 3 passed / 68 намеренных TODO xfail; Ruff/mypy 18 файлов чистые |
| HF Trainer и NER | Настоящие локальные random BERT, Datasets.map, collator, Trainer checkpoint/resume; дополнительно safe reload/fingerprint и отклонение forward-only/no-update решения | После усиления gate: 13 passed / 29 TODO/artifact xfail; Ruff/mypy 19 файлов чистые |
| SFT/LoRA | Фактический dataloader и causal masked loss, PEFT adapter update/reload, UTF-8, bool/number JSON и tokenizer/template identity | После усиления gate: 24 passed / 1 TODO xfail; стандартный strict mypy 20 файлов чистые |
| Reranking и embeddings | Реальные CrossEncoder/SentenceTransformer API на маленькой локальной модели; отдельно общий UTF-8 report budget до загрузки модели | Исходный срез 33 passed / 27 TODO xfail; исправление budget: 37 pure passed, mypy 19 файлов чистые |
| MLflow/Optuna | Реальный четырёхtrial CPU workflow с SQLite и reload; проверка fitted state и сохранённых trials/runs | Первый API smoke прошёл; окончательный вариант с последующими изменениями также прошёл общий прогон ниже |
| Optional group diagnostics | Неверные группы, отсутствующие транзитивные модули, общая команда sync, сохранение pytest exit codes | 76 tooling tests passed; отдельный RED перед реализацией: 10 failures |
| vLLM offline assessment | Ограниченный reader/hash/identity, raw arithmetic consistency и отказ на NOT_RUN/synthetic/malformed evidence | 17 passed / 1 missing-live skip / 6 TODO xfail; сервер не вызывался |

Изменённые starter tests сохраняют `NotImplementedError` и intentional xfail.
Это не положительный learner результат. Отдельные тесты библиотечных author
примеров не входят в новые completion targets.

## Интегрированная проверка

Метаданные, tooling и repository hygiene: **75 passed / 23 deselected**;
отдельно Markdown links **3 passed**, maintainer-only starter policy **4 passed**.
Общая изменённая инфраструктура: стандартный strict mypy **13 файлов clean**,
Ruff check/format clean. Исходные 180 parsed catalog records сравнены с parent:
совпадают; старый текст progress сохранён.

Отрицательные CLI проверки подтверждают, что незавершённые задания не дают зачёт:
`data-vectorized-features` и `lab-vllm-measurements` возвращают exit 1;
`lab-sft-lora` в base environment возвращает exit 2 и полную инструкцию установки
недостающей группы. Полный `check-track` с незаполненными заданиями не запускался.

Один общий прогон всех 11 новых каталогов в установленном CPU environment:
**140 passed, 1 skipped, 153 xfailed за 13,45 секунды**. Включены
`ROADMAP_RUN_SFT=1`, `ROADMAP_RUN_RANKING=1`, `ROADMAP_RUN_EXPERIMENTS=1`,
HF offline/telemetry flags и один CPU thread для численных библиотек.
Проверялись фактические Trainer/TRL/PEFT/Sentence Transformers/MLflow/Optuna API,
а не только наличие optional пакетов. Общий прогон выполнен один раз.

Точные pytest scopes:

```bash
.venv-training/bin/python -m pytest \
  modules/03_data_foundations/exercises/vectorized_features \
  modules/03_data_foundations/exercises/point_in_time_features \
  modules/04_machine_learning/exercises/sklearn_selection \
  labs/02_huggingface_models/trainer_workflow \
  labs/02_huggingface_models/token_classification \
  labs/04_llm_finetuning/sft_workflow \
  labs/01_pytorch_foundations/exercises/training_efficiency \
  labs/03_real_rag/neural_reranking \
  labs/03_real_rag/embedding_adaptation \
  projects/document_intelligence_lab/experiment_management \
  labs/05_model_serving/assessment -q --tb=short
```

Команда показана для Linux interpreter и предполагает перечисленные flags.
На Windows используется `.venv-training/Scripts/python.exe`; hosted проверка
своей платформы выполняется CI, а не выводится из этого Linux результата.
Один skip — отсутствующее реальное vLLM evidence; 153 xfail — незаполненные
learner boundaries/артефакты. Строгий `check` считает их незавершёнными.

Все изменённые Python-файлы: **Ruff check clean / 102 files already formatted**.
Все новые scopes и изменённая общая инфраструктура: стандартный project strict
**mypy clean, 108 source files**. Проверка не использует ослабляющие mypy flags.

По каждому из шести направлений выполнено отдельное ревью; все обнаруженные
блокирующие замечания устранены и проверены повторно в пределах исправления.
Финальное ревью всей ветки не выявило оставшихся Critical/Important замечаний.

После него одним небольшим исправлением закрыты пять замечаний: проверка
массивов NER-разметки, полнота train-query triples до загрузки encoder,
finite loss/adapter перед QLoRA execution status, усечение tied top-k и
сохранение отрицательной permutation importance. Точечный covering run:
**33 passed / 43 intentional TODO xfail за 2,71 секунды**; strict mypy
**46 source files clean**, Ruff/format **8 изменённых файлов clean**.
Это отдельная проверка изменённых мест, а не повтор общего прогона.

Новые assessment cases проверены временными контрольными вариантами:
arbitrary tied `argpartition` subset отклоняется при k=1 и k=3; clipping отрицательной
importance отклоняется на фиксированном fitted-model fixture. Его независимый
reference mean равен `[-0.6666666666666666, 0.0]`; это учебные данные, не результат
внешней модели. Эти варианты не сохранены как готовые learner implementations.
QLoRA postconditions проверялись только на CPU safetensors; GPU recipe не выполнялся.

Три небольших улучшения покрытия оставлены явно, без заявления об исчерпывающем
доказательстве корректности любого будущего решения:

- В SFT unit test можно отдельно усилить полноту validation-части и неизменность
  входных записей. Полный, уникальный, family-disjoint split уже проверяется
  live evidence gate.
- В accumulation test можно дополнительно параметризовать train/eval mode и
  проверить сохранение режима вызывающего кода. Сейчас проверяются два обновления,
  loss, gradients, параметры и momentum, включая неравные micro-batches.
- В experiments можно исчерпывающе закрепить все фиксированные defaults pipeline
  и допустимые значения n-gram во всех trial records. Сейчас проверяются реальные
  ordered fit/predict, применение C/ngram, seed, stores и воспроизведение fitted
  state на train. Например, отдельное требование `max_iter=100` ещё не является
  механическим gate для каждого сохранённого решения.

Эти пункты — дальнейшее усиление тестов и узкого протокола; они не заменяют
обязательную проверку решения и объяснений человеком.

## Hosted CI

После push workflow выполняет base checks на Ubuntu/Windows и отдельный Windows
CPU job с установленными `trainer/sft/ranking/experiments`. Этот файл фиксирует
локальное состояние **до** push; результат конкретного опубликованного commit
проверяется в [запусках ветки](https://github.com/DmitriyGrachev/Ml_roadmap/actions?query=branch%3Anamepfchekcoutbranch-extended-pa1).
Настройка CI и зелёный результат родительского commit не являются результатом PA1.

## Что остаётся невыполненным учеником

- Собственные решения новых starter functions и независимый перенос на новый домен.
- Настоящие pretrained Trainer/NER/SFT/embedding/reranking исследования с корректным
  holdout, сохранёнными predictions/model artifacts и разбором ошибок.
- Собственный MLflow/Optuna поиск и защита выбора, а не запуск author fixture.
- Реальные GPU/AMP/CUDA memory/time измерения и QLoRA; случайная CPU модель их не заменяет.
- Linux/vLLM serving, restart, streaming/cancellation и измерения; статус остаётся
  **NOT_RUN / DEFERRED_ENV**, соответствующий обязательный gate не закрыт.
- Человеческая проверка происхождения артефактов, авторства и объяснений:
  **REQUIRES_REVIEW**.

Тестовые числовые fixtures помечены synthetic/random mechanism. Реальных метрик
качества или скорости новой pretrained модели этот commit не заявляет.
