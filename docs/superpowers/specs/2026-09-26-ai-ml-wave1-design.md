# Первая волна AI/ML: согласованная архитектура

Исходный commit: `03a729bc3952df39793d8ccbdbbf64b08d6a123f` (`main`).
Пользователь подтвердил архитектуру и поручил реализацию с уточнениями 26.09.2026.

## Границы

Расширяем существующий репозиторий, каталог и CLI. Сохраняем все существующие
упражнения и ручной progress. Новые пояснения — по-русски, Python identifiers —
по-английски. Не публикуем решения student TODO. Никаких model/data downloads
при import, pytest или uv sync. Не выполняем commit/push в этой итерации.

## Проверки

`test ID` сохраняет health-смысл: незавершённые задания могут быть xfail.
`check ID` запускает только выбранные catalog targets через тот же pytest runner,
возвращает ненулевой код при failures, обязательных skips/xfails, zero collected
и отсутствии обязательных результатов. Optional live/GPU остаётся NOT_RUN;
успешный offline check не означает LIVE_VERIFIED или качество модели.
Регрессии проверяем на временных учебных fixtures, не решениях настоящих задач.

## Окружение

По последнему требованию пользователя используется opt-in dependency group
`training`, а не отдельный проект. `uv sync` устанавливает существующую базу
и dev; `uv sync --group training` добавляет CPU PyTorch, Transformers, Datasets.
Версии фиксируем после фактического разрешения. Не добавляем MLflow, PEFT, vLLM
или CUDA в первую волну. Базовая collection не требует training-библиотек.

## Учебный слой

- Короткий `modules/04_machine_learning/07_training_bridge`: ссылки на существующие
  NumPy/regression/split/metrics, loss → gradient → descent → autograd, небольшой
  незаполненный gradient/update контракт, протокол данных и эксперимента.
- `labs/01_pytorch_foundations`: Dataset/DataLoader, Module, полный training/validation
  lifecycle, train/eval, debugging, checkpoint/reload/inference. Соседний runnable
  CPU-пример не решает упражнения. Локальные синтетические изображения предметов
  — smoke, не свидетельство прикладного качества.
- `labs/02_huggingface_models`: tokenizer/preprocessing/batching, настоящий encoder,
  frozen embeddings vs classical baseline vs bounded adaptation, evaluation,
  save/load/inference. Маленький случайный локальный encoder допустим только для
  offline механического smoke с явной маркировкой, не для quality evaluation.
- Student starters сохраняют NotImplementedError. Артефакты и отчёты создаёт ученик;
  проверки различают структуру, вычисленные метрики и его собственный анализ.
- Остальные labs и Document Intelligence Lab — только PLANNED specifications.

## Воспроизводимость и безопасность

Фиксируем seed, параметры, package/model/data revisions, split IDs и checksums,
реальные метрики; не требуем универсального accuracy или одинаковых GPU/CPU чисел.
Загрузки только отдельной явной командой, public ungated ресурсы, safetensors,
trust_remote_code=False. Download/cache/weights/reports не коммитим.

## Приёмка

Полный regression, Ruff check/format, настроенный mypy, base и training installs,
CPU offline smoke, negative strict-check на untouched задачах, positive checker
fixtures. Проверяем Markdown links и существующие четыре notebook examples.
NOT_RUN для настоящего model download/evaluation, GPU, Colab, vLLM, cloud.
