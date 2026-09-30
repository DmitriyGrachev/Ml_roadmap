# Первая волна: фактические проверки

Дата: 26.09.2026. Статус: **VERIFIED для перечисленных offline проверок**.
Учебные материалы первой волны READY; pretrained evaluation остаётся NOT_RUN.
Это журнал сопровождающего, не progress ученика. Исходная версия
`03a729bc3952df39793d8ccbdbbf64b08d6a123f`; работа в `codex/ai-ml-wave1` без публикации.

## До изменений

Windows, Python 3.12.14: pytest 659 passed, 5 skipped, 1056 xfailed, 1 предупреждение
Starlette/AnyIO; Ruff clean, 614 files formatted, mypy 519 sources. Все исходные
student tasks остаются незаполненными; текущие markers progress — `[ ]`.

## Окружения

`uv lock` и `uv sync --locked`: успешны. Locked packages 192 (до добавления 161).
Версии ранее имевшихся packages не изменились.
В базовой `.venv` отсутствуют distributions torch/transformers/datasets.

Отдельное проверочное окружение того же проекта:

```powershell
$env:UV_PROJECT_ENVIRONMENT = "$PWD/.venv-training"
uv sync --locked --group training
```

Установка успешна: torch 2.14.0+cpu (CUDA=None), transformers 5.17.0, datasets 5.0.1.
Это установка библиотек, не загрузка pretrained weights/dataset.
Переменная выше нужна только для проверки сопровождающего. Для учёбы используйте
обычную `.venv` и `uv run --group training ...`, как в [compute guide](compute-guide.md).

## Результаты regression и quality checks

Команды ниже выполнены в Windows, Python 3.12.14, из корня проекта.

| Проверка | Команда | Фактический результат |
| --- | --- | --- |
| Полный base regression | `.venv/Scripts/python.exe -m pytest -q` | **703 passed, 30 skipped, 1074 xfailed**, exit 0; 98.04 s |
| Полный training regression | `.venv-training/Scripts/python.exe -m pytest -q` | **727 passed, 5 skipped, 1093 xfailed**, exit 0; 107.02 s |
| Strict checker fixtures | `.venv/Scripts/python.exe -m pytest tests/tooling/test_check.py -q` | **19 passed**, exit 0 |
| Ruff | `.venv/Scripts/python.exe -m ruff check .` | All checks passed, exit 0 |
| Форматирование | `.venv/Scripts/python.exe -m ruff format --check .` | **654 files already formatted**, exit 0 |
| Базовый mypy | `.venv/Scripts/python.exe -m mypy` | **524 source files**, без ошибок |
| Training mypy | `.venv-training/Scripts/python.exe -m mypy -p labs` | **24 source files**, без ошибок |
| Новая PyTorch lab | `.venv-training/Scripts/python.exe scripts/learn.py check lab-pytorch` | **19 passed, 14 xfailed**, exit 1 — намеренно незавершённые задания/отчёт |
| Новая HF lab | `.venv-training/Scripts/python.exe scripts/learn.py check lab-huggingface` | **24 passed, 9 xfailed**, exit 1 — намеренно незавершённые задания/отчёт |
| Повторная HF проверка после последней правки | `.venv-training/Scripts/python.exe -m pytest labs/02_huggingface_models -q` | **24 passed, 9 xfailed**, exit 0 |

`xfail` — невыполненные задания, не выполненные проверки качества модели.
Разница skips между окружениями ожидаема: в базе нет training libraries; пять
прежних skips сохранены в training. Оба полных прогона содержат одно исходное
предупреждение Starlette о deprecated AnyIO BlockingPortal alias; новых warnings нет.

Полный suite также включает структуру/исполнение четырёх существующих notebooks,
catalog/navigation contracts и сохранность старых student boundaries. Дополнительно
проверены **195 Markdown-файлов**, включая новые незакоммиченные: **0 broken local links**.
`git diff --check` — без ошибок. В каталоге 148 entries:
57 lessons, 88 exercises, 1 существующий project и 2 labs.

Проверка смысла CLI на реальных IDs:

- `test python-word-index`: 13 xfailed, exit 0; `check python-word-index`: те же
  13 xfailed, exit 1. Стартер оставлен нетронутым.
- `check ml-training-bridge`: 1 passed, 14 xfailed, exit 1.
- `check python-environment` из соседней папки: 31 passed, exit 0; TODO других
  заданий не мешают выбранному ID. Это проверка примеров, не отметка progress.
- `check lab-pytorch` без training: понятная ошибка отсутствующей зависимости,
  ненулевой exit; не ложный PASS/зачёт.

## Разделение свидетельств

- **Unit/contract tests:** арифметика, shape/dtype, split/masks, режимы модели,
  градиенты, состояние optimizer, контракт JSON и вычисление метрик.
- **Integration/CPU smoke:** настоящие операции PyTorch/Transformers на маленьких
  локальных данных; сохранение и повторная загрузка реальных файлов.
- **ML evaluation:** ваши измерения и анализ на зафиксированных данных. Для pretrained
  MiniLM/Bitext пока NOT_RUN. Никакого универсального порога accuracy для зачёта нет.

Примеры запущены из корня:

```powershell
.venv/Scripts/python.exe -m modules.04_machine_learning.07_training_bridge.example
.venv-training/Scripts/python.exe -m labs.01_pytorch_foundations.example
.venv-training/Scripts/python.exe -m labs.02_huggingface_models.example
```

Мост: loss уменьшился с 2.56 до 0.042998... за пять показанных шагов.
PyTorch: 19 train / 7 validation, две эпохи, семь предсказаний,
`checkpoint_reloaded=true`, `quality_claim=false`.
HF: случайный локальный encoder, logits `[2,2]`, два padding-токена,
`finite_logits=true`, `reload_max_abs_difference=0.0`, `pretrained_quality=NOT_RUN`.

## Независимая проверка и сохранность

Review воспроизвёл и помог закрыть следующие ошибки проверки:

- `--collect-only`, `--setup-only` и `-k` через PYTEST_ADDOPTS больше не дают
  ложный зачёт: нужны успешные setup/call/teardown каждого обязательного теста.
- Пробы во время forward проверяют train/eval и режим градиентов, а не только
  окончательное состояние модели.
- Checkpoint проверяется на загрузку и совместимость, включая восстановление
  learning rate и заполненных momentum buffers, не только наличие файла.
- HF comparison проверяет фактические fit/pooling/adaptation/inference и сверяет
  предсказания с сохранённой моделью. Пропущенные learning_rate/preprocessing
  отклоняются; полностью выполненный протокол не обязан давать высокую accuracy.
- Windows local CSV path проверен через `csv.DictReader` и `Dataset.from_list`:
  это обходит обнаруженный длинный cache-lock путь, не загружая внешний dataset.
- Новое training-окружение, cache и веса исключены и из Git, и из Docker context.

Сравнение с исходным commit подтвердило: старые реализации/тесты упражнений,
Banking AI Lab и данные не изменены. В старом Module 04 README добавлена только
навигация к мосту и уточнён критерий завершения. Исходный текст progress сохранён
как префикс; добавлены только три `[ ]`. Ни один урок ученику не засчитан.
Версии всех ранее имевшихся locked packages сохранены.

## Новые файлы

Перечень первой волны (пути относительно корня):

```text
docs/skills-matrix.md
docs/ai-ml-extension-plan.md
docs/compute-guide.md
docs/experiment-protocol.md
docs/wave1-verification.md
docs/superpowers/specs/2026-09-26-ai-ml-wave1-design.md
docs/superpowers/plans/2026-09-26-ai-ml-wave1.md
src/roadmap_tools/strict_check.py
tests/tooling/test_check.py
modules/04_machine_learning/07_training_bridge/
    README.md, __init__.py, example.py, starter.py, test_bridge.py
labs/
    __init__.py, conftest.py, test_offline_contract.py
labs/01_pytorch_foundations/
    README.md, example.py, starter.py, report.py
    test_example.py, test_starter.py, test_report.py
labs/02_huggingface_models/
    README.md, __init__.py, example.py, starter.py, local_fixture.py
    protocol.py, resources.json, download.py, run.py
    test_example.py, test_starter.py, test_protocol.py
labs/03_real_rag/README.md
labs/04_llm_finetuning/README.md
labs/05_model_serving/README.md
labs/06_ml_lifecycle/README.md
projects/document_intelligence_lab/README.md
```

Общие изменения: существующие CLI/catalog, curriculum, README/roadmap/setup/testing,
progress, pyproject/lock, Git/Docker exclusions и regression contracts. Новый runner,
веб-интерфейс и платформа tracking не создавались. `check` — plugin к тому же pytest;
три новых catalog ID: `ml-training-bridge`, `lab-pytorch`, `lab-huggingface`.

## Откуда начать учёбу

Если начинаете Python с нуля, откройте
[Environment and workflow](../modules/01_python_core/00_environment/README.md).
Не начинайте с тяжёлых библиотек. В PowerShell:

```powershell
Set-Location C:\ProjectsDirectory\AIML\_road
uv sync --locked
uv run python scripts/learn.py validate-env
uv run python scripts/learn.py test python-environment
```

После object model и collections — нейтральный
[word index](../modules/01_python_core/exercises/word_index/README.md).
Реализуйте его starter, затем выполните:

```powershell
uv run python scripts/learn.py test python-word-index
uv run python scripts/learn.py check python-word-index
```

`test` может быть зелёным при TODO; `check` до реализации ожидаемо ненулевой.
После перечисленных в мосте prerequisites:

```powershell
uv run python scripts/learn.py test ml-training-bridge
uv run python scripts/learn.py check ml-training-bridge
uv sync --locked --group training
uv run --group training python -m labs.01_pytorch_foundations.example
uv run --group training python scripts/learn.py test lab-pytorch
uv run --group training python scripts/learn.py check lab-pytorch
uv run --group training python -m labs.02_huggingface_models.example
uv run --group training python scripts/learn.py test lab-huggingface
uv run --group training python scripts/learn.py check lab-huggingface
```

В labs самостоятельно пишете функции из starter, связываете обучение и оценку,
создаёте snapshot/split/checkpoint и собственный отчёт с анализом ошибок.
Скачивание ресурсов HF — отдельная команда в lab02, не часть старта выше.

## NOT_RUN

- Pretrained MiniLM/Bitext download, fine-tuning/evaluation на этих данных:
  не запускались; последнее требование пользователя допускает загрузку только
  его отдельной явной командой.
- CUDA/GPU, Linux/WSL, Colab, vLLM, real RAG/vector DB, MLflow, cloud/deployment:
  не запускались, не относятся к VERIFIED первой волны.
- Ученические отчёты/решения/анализ не созданы агентом; зачёт ученика не выставлен.
