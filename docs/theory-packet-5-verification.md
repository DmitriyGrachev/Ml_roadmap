# Теоретический пакет 5 — материалы и проверка

Дата: 04.10.2026. Репозиторий `C:\ProjectsDirectory\AIML\_road`, ветка
`codex/ai-ml-wave1`, HEAD `836028944eceaa260cb47d0056b593af4a4648d4`.
Пакет углубляет две существующие лабораторные, не добавляет новый курс.
Часть А реализована и проверена до начала реализации Б. Commit/push/merge
не выполнялись. Понимание ученика **НЕ ПРОВЕРЕНО**.

## С чего начать

Сначала откройте [PyTorch README](../labs/01_pytorch_foundations/README.md),
затем [теорию части А](../labs/01_pytorch_foundations/theory.md).
Прежние prerequisites остаются: NumPy → ML → математический мост → PyTorch.

1. Предскажите формы, вручную пройдите одну картинку через слои и loss.
2. Разберите граф и шесть производных, рассчитайте обновление одного веса и bias.
3. Запустите преподавательскую трассу А; сравните свои числа с `trace.json`.
4. Объясните modes, короткий батч, validation и разницу inference/resume.
5. Выполняйте свой прежний `lab-pytorch`, затем resume/diagnostics по их prerequisites.
6. Перед HF-заданиями откройте [HF README](../labs/02_huggingface_models/README.md)
   и [теорию части Б](../labs/02_huggingface_models/theory.md). Сначала токены и
   формы, затем ручная строка attention, маски и Transformer-блок.
7. Запустите трассу Б, объясните контролируемое изменение padding/value,
   затем решайте прежние HF/attention TODO. Демонстрации не являются submission.

### Подготовка двух существующих окружений

Команды ниже — из PowerShell, из корня репозитория. Установка пакетов может
использовать сеть, если кеш пуст; сами демонстрации моделей/датасетов не скачивают.
Новые версии библиотек этим пакетом не добавлены. База остаётся без training
и visualization; второе существующее окружение содержит обе opt-in группы.

```powershell
Set-Location C:\ProjectsDirectory\AIML\_road
$packet5PreviousEnvironment = $env:UV_PROJECT_ENVIRONMENT
try {
    $env:UV_PROJECT_ENVIRONMENT = ".venv"
    uv sync --locked
    $env:UV_PROJECT_ENVIRONMENT = ".venv-training"
    uv sync --locked --group training --group visualization
} finally {
    $env:UV_PROJECT_ENVIRONMENT = $packet5PreviousEnvironment
}
```

Для текста/чисел без графиков достаточно `--group training` во второй установке.
При проверке сопровождающего обе установки дополнительно использовали `--offline`
и успешно взяли пакеты из кеша. Это не требование иметь кеш при первом старте.
После установки прямой вызов выбранного interpreter не пересинхронизирует группы.
Третьего окружения, notebook, виджетов, новых зависимостей нет.

### Запуски ученика

Выбирайте **новые** имена каталогов; существующие, даже пустые, отвергаются.
Не удаляйте старые результаты ради повторного запуска.

```powershell
.venv-training/Scripts/python.exe -m labs.01_pytorch_foundations.walkthrough --output generated-reports/my-teacher-a-01 --plots
.venv-training/Scripts/python.exe -m labs.02_huggingface_models.walkthrough --output generated-reports/my-teacher-b-01 --plots
```

Можно убрать `--plots`: все числа сохранятся в JSON, Matplotlib не импортируется.
В А получатся `trace.json`, `snapshot.json`, `shape-smoke.pt`, опционально
`learning.png`; в Б — `trace.json`, `local-model/` с локально созданными
safetensors/config/tokenizer, опционально `attention.png`.
Полоска `Loading weights` здесь означает чтение **локального** сохранённого файла,
а не скачивание pretrained модели. Явную download-команду исходной HF lab не запускали.

После собственной реализации используйте прежний CLI, например:

```powershell
.venv-training/Scripts/python.exe scripts/learn.py test lab-pytorch
.venv-training/Scripts/python.exe scripts/learn.py check lab-pytorch
.venv-training/Scripts/python.exe scripts/learn.py test lab-huggingface
.venv-training/Scripts/python.exe scripts/learn.py check lab-huggingface
.venv-training/Scripts/python.exe scripts/learn.py test lab-attention-mechanics
.venv-training/Scripts/python.exe scripts/learn.py check lab-attention-mechanics
```

`test` допускает ожидаемые xfail незавершённых заданий; `check ID` проверяет
именно вашу работу и её прежний контракт. Новая теория и author tests не
расширяют старый check и не обновляют progress. Эти команды зачёта приведены
как маршрут ученика, а не как утверждение, что задания выполнены.

## Новые и изменённые файлы

Семь новых файлов:

- [PyTorch theory.md](../labs/01_pytorch_foundations/theory.md).
- [PyTorch walkthrough.py](../labs/01_pytorch_foundations/walkthrough.py).
- [HF theory.md](../labs/02_huggingface_models/theory.md).
- [HF walkthrough.py](../labs/02_huggingface_models/walkthrough.py).
- [Авторские проверки PyTorch](../labs/test_packet5_pytorch.py).
- [Авторские проверки HF/attention](../labs/test_packet5_huggingface.py).
- Этот единый отчёт.

Четыре изменённых существующих файла: README
[lab01](../labs/01_pytorch_foundations/README.md),
[lab02](../labs/02_huggingface_models/README.md),
[attention](../labs/02_huggingface_models/attention_mechanics/README.md)
(только ссылки на теорию), [карта покрытия](wave2-coverage.md#theory-packet-5)
(добавлен раздел, история сохранена).

Почему отдельные walkthrough: старые `run_smoke` имеют проверяемые компактные
контракты. Новые traces добавляют промежуточные измерения, не меняя эти контракты.
А переиспользует `ShapeImages/ShapeNet`, Б — `make_local_components/run_smoke`.
Нет generic-решений `train_epoch`, `masked_mean_pool`, `attention` со всеми
ученическими проверками, второго resume-формата или готового расследования A–D.
Численные демонстрации полностью разобраны; анализ ученика остаётся его работой.
Тесты находятся в `labs/test_packet5_*.py`, вне действующих curriculum targets.

## Техническая проверка

Проверено на Windows, Python 3.12.14, PyTorch 2.14.0+cpu,
Transformers 5.17.0, Datasets 5.0.1, Matplotlib 3.11.2 (только training+visualization).
`pyproject.toml` и `uv.lock` сохранены относительно начала пакета.

| Реальная команда или проверка | Результат |
| --- | --- |
| `.venv` → `uv sync --locked --offline` | Exit 0; `torch`, `transformers`, `matplotlib` отсутствуют по `find_spec` |
| `.venv-training` → `uv sync --locked --offline --group training --group visualization` | Exit 0; существующие закреплённые зависимости |
| `.venv/Scripts/python.exe -m pytest -q` | 970 passed, 50 skipped, 1160 xfailed; 111.34 s, без падений |
| `.venv-training/Scripts/python.exe -m pytest -q -rs` | 1077 passed, 6 skipped, 1224 xfailed; 150.25 s, без падений |
| `.venv-training/Scripts/python.exe -m pytest labs/test_packet5_pytorch.py labs/01_pytorch_foundations -q` | 87 passed, 37 xfailed; выполнено до Б |
| `.venv-training/Scripts/python.exe -m pytest labs/test_packet5_huggingface.py labs/02_huggingface_models -q` | 31 passed, 31 xfailed |
| `.venv-training/Scripts/python.exe -m pytest labs/test_packet5_pytorch.py labs/test_packet5_huggingface.py -q` | 11 passed, включая оба PNG и отказ перезаписи |
| `.venv/Scripts/python.exe -m ruff check .` | All checks passed |
| `.venv/Scripts/python.exe -m ruff format --check .` | 825 files already formatted |
| `.venv/Scripts/python.exe -m mypy` | Success, 627 source files |
| `.venv-training/Scripts/python.exe -m mypy -p labs` | Success, 52 source files |
| `git diff --check` | Exit 0 |

В training-прогоне пропущены две проверки symlink, недоступных без прав Windows,
и четыре интеграционные проверки PostgreSQL без `ROADMAP_POSTGRES_URL`.
Базовая среда дополнительно пропускает optional training/visualization проверки.
В полной регрессии есть одно существующее `DeprecationWarning` Starlette об
устаревающем имени AnyIO `BlockingPortal`; оно не подавлялось и не исправлялось
несвязанным изменением. Xfail не выданы за решённые упражнения.

Разработка проверок шла до кода: первые запуски фиксировали отсутствие новых
демонстраций. Тест сериализации затем выявил отличие integer-ключей `id2label`
от JSON string-ключей; исправлено через стандартный JSON config Transformers.
Добавлено явное seed-значение локальной фабрики. При параллельной подготовке
документов ещё один повтор обеих регрессий зафиксировал одну ошибку
`test_every_tracked_local_markdown_link_resolves`: новая ссылка в карте уже
появилась, а файл этого отчёта ещё создавался. После создания отчёта ссылка
разрешается; финальная регрессия выполняется на полном наборе документов.
Финальные результаты не скрывают эти промежуточные неудачи разработки.

### Наблюдаемые числа и изображения

Автор реально выполнил команды двух walkthrough с `--plots` и новыми каталогами
`generated-reports/teacher-packet5-a-verified-02` и
`generated-reports/teacher-packet5-b-verified-02`. Это игнорируемые преподавательские
outputs, не новые ученические отчёты.

- А: CE `0.31326168751822286`; выбранный gradient `−0.2689414213699951`,
  конечная разность `−0.2689414213691288`; после двух backward без очистки
  `−0.5378828427399902`. После одного SGD `W₁[0,1]=1.0268941421369995`;
  новый loss `0.2716702022440425`. Совпадение не является обещанием монотонности
  любого обучения. Последние батчи train/validation — 1/1 строка; reload delta 0.
- Б: attention output `[1.4621171572600098,1.0757656854799806]`;
  отличие от ручного расчёта около `2.22e-16`; замена закрытого value — delta 0.
  BERT logits `[2,2]`; pooler/head delta 0, замена masked ID — delta 0,
  открытие этих позиций — около `2.47e-5`, single/batch — около `9.31e-10`.
  Это наблюдения фиксированной CPU-конфигурации, не универсальные пороги качества.
- `learning.png` и `attention.png` построены из трасс и открыты для визуального
  осмотра: подписи/оси/маска читаются, обрезанных подписей не обнаружено.
  Train loss измеряется online, validation — после эпохи; это явно подписано.
  Attention heatmap не названа причинным объяснением ответа модели.
- Диаграммы/формулы сопоставлены с кодом и числовыми tests. Официальные ссылки
  на PyTorch 2.14/HF 5.17 проверены; для удалённого versioned padding guide
  честно указан текущий официальный guide с локально проверенным поведением.
- У семи документов проверены 96 локальных ссылок, в том числе 12 якорей,
  и парность code fences. Проверка карты ограничена добавленным разделом,
  история не переписана. Это проверка структуры, не браузерного отображения.
  Обе теории и отчёт также преобразованы установленным Mistune в HTML в памяти:
  семь таблиц имеют согласованное число столбцов; заголовки и code blocks
  распознаются. Установка Markdown-библиотек для этой проверки не потребовалась.

### Сохранность и границы проверки

В начале записаны SHA-256 861 существующего tracked/untracked неигнорируемого файла.
Из них изменились только четыре перечисленных документа; остальные **857**,
включая предыдущие пакеты, learner TODO/реализации, curriculum, CLI, зависимости
и progress, остались побайтно прежними. Новых файлов — семь. Игнорируемые
виртуальные среды и новые teacher outputs в этот исходный снимок не входят.
SHA-256 `progress.md`: `9C78D95D05EFB7234C8B3412D072577916A11192531AEE1B27A0DF60CE647DC0`.

Независимые read-only review А и всего пакета не нашли блокирующих замечаний.
Авторские tests выполнялись с существующим запретом socket-соединений в labs;
реальные Hub weights/datasets не скачивались. Формат checkpoint resume,
контракт attention и старые требования зачёта не менялись.

**NOT_RUN:** GPU/CUDA, Linux, реальные pretrained experiments, PyCharm UI,
браузерный rendering Markdown. PNG просмотрены отдельно; это не проверка всех
возможных Markdown-редакторов. Автоматического экзаменатора понимания нет.
Зачёт собственных learner TODO/reports и содержательная защита — **REQUIRES_REVIEW**.
Следующее углубление LLM Engineering/RAG и реальные будущие labs остаются **PLANNED**.
