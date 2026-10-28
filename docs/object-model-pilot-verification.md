# Object Model: проверка теоретического пилота

Дата: 2026-10-02. Рабочая копия: `C:\ProjectsDirectory\AIML\_road`.
Ветка: `codex/ai-ml-wave1`; исходный HEAD:
`836028944eceaa260cb47d0056b593af4a4648d4`. До работы tracked/untracked diff отсутствовал.
Среда: Windows, PowerShell, базовая `.venv`, Python 3.12.14, uv 0.12.17.
Новые зависимости не устанавливались; модели, датасеты и training environment не требовались.

## Где начать

Откройте [README урока](../modules/01_python_core/01_object_model/README.md),
затем [теорию](../modules/01_python_core/01_object_model/theory.md).
Порядок: прочитать ситуацию → записать прогноз → разобрать схемы → выполнить код →
объяснить отличия от прогноза → проверить вариацию → самопроверка → существующее
упражнение после его prerequisites. Переходы на задания и их ID находятся в теории.

Из корня проекта:

```powershell
uv run --offline --no-sync python modules/01_python_core/01_object_model/example.py
```

## Изменённые и новые файлы

Изменены:

- [README.md](../modules/01_python_core/01_object_model/README.md) — вход и маршрут.
- [example.py](../modules/01_python_core/01_object_model/example.py) — последовательная
  демонстрация; прежняя функция `compare_ticket_tags()` и её результат сохранены.
- [test_examples.py](../modules/01_python_core/tests/test_examples.py) — три проверки
  фактического вывода новых шагов, без ученических решений.

Добавлены:

- [theory.md](../modules/01_python_core/01_object_model/theory.md) — подробное объяснение.
- [bindings.svg](../modules/01_python_core/01_object_model/assets/bindings.svg),
  [mutation.svg](../modules/01_python_core/01_object_model/assets/mutation.svg),
  [rebinding.svg](../modules/01_python_core/01_object_model/assets/rebinding.svg),
  [shallow_copy.svg](../modules/01_python_core/01_object_model/assets/shallow_copy.svg).
- [theory-lesson-template.md](theory-lesson-template.md) — только шаблон, не массовая переделка.
- Этот отчёт.

README сохраняет проверяемые заголовки и переход в Collections. Прямые ссылки
на подходящие задания размещены в теории, без изменения каталога и учебного порядка.
Статичные локальные схемы и существующий пример обходятся без отдельного интерфейса.

## Реальные проверки

Все команды ниже запускались из корня рабочей копии; `--offline --no-sync`
исключает сетевую синхронизацию окружения.

| Команда / действие | Результат |
| --- | --- |
| `uv run --offline --no-sync python modules/01_python_core/01_object_model/example.py` | 10 строк; полный вывод совпал с опубликованным |
| `uv run --offline --no-sync pytest modules/01_python_core/tests/test_examples.py -q -k object` | Сначала 3 новых теста упали из-за отсутствующего поведения; после реализации 6 passed |
| `uv run --offline --no-sync pytest modules/01_python_core/tests/test_examples.py modules/01_python_core/tests/test_learning_flow.py -q` | 64 passed |
| `uv run --offline --no-sync pytest -q` | 927 passed, 39 skipped, 1160 xfailed; 1 warning |
| `uv run --offline --no-sync ruff check .` | All checks passed |
| `uv run --offline --no-sync ruff format --check .` | 783 files already formatted |
| `uv run --offline --no-sync mypy` | No issues found in 609 source files |
| `git diff --check` | Нет ошибок whitespace |

Предупреждение полного прогона — `DeprecationWarning` из Starlette testclient
о `anyio.abc.BlockingPortal`. Skips/xfails не объявлены выполненными заданиями.
Training/GPU/live-проверки отдельно не запускались: **NOT_RUN**, вне изменений пилота.

Одноразовая локальная QA-проверка в игнорируемом
`generated-reports/object-model-pilot/verify_pilot.py` выполнена командой
`uv run --offline --no-sync python generated-reports/object-model-pilot/verify_pilot.py`.
Она сверила восемь независимых Python-фрагментов теории, полный вывод файла,
36 локальных ссылок/якорей/изображений и XML четырёх SVG. Это не новый test/check target.

Визуально открыты локальный Markdown-предпросмотр README/theory, все четыре SVG,
таблица Java и раскрывающиеся ответы; проверен переход к Self-check. Подпись L3,
выходившая из блока, сокращена и повторно проверена. Предпросмотр временный,
через установленный Mistune и встроенный браузер; это **не** проверка идентичного
отображения в GitHub или PyCharm. Их интерфейсы — **NOT_RUN**. Windows CLI запуск проверен.

Два основных ресурса — [Python Tutorial §9.1](https://docs.python.org/3.12/tutorial/classes.html#a-word-about-names-and-objects)
и [Python Tutor](https://pythontutor.com/). Страницы и точечные официальные
семантические ссылки открыты веб-инструментом 2026-10-02; подробности и границы
чтения указаны в теории. Выполнение в Python Tutor — **NOT_RUN**, код туда не отправлялся.

## Сохранность и границы результата

Ученические реализации/TODO, контракты их тестов, `curriculum.toml`, CLI,
`pyproject.toml`, `uv.lock` и `progress.md` не изменены. Сохранность исходных
tracked-файлов вне трёх перечисленных изменений сверена по SHA-256.
Из 806 исходных tracked-файлов 803 побайтно неизменны; изменены только три файла выше.
Прежние отметки progress сохранены; новый учебный материал не означает прохождение.
Commit/push/merge не выполнялись. Временные QA-файлы остаются в игнорируемой папке.

Независимое ревью сверило содержание, код и схемы. Замечание о требовании
вложенных списков в обязательной самопроверке устранено: эта тема остаётся
необязательной. Смысловая точность проверена в указанном объёме; понятность
для конкретного ученика всё ещё требует его обратной связи.

Работа ограничена Object Model. Следующие кандидаты после оценки пилота —
NumPy (shape/axis/broadcasting) и математический мост (loss/градиент/chain rule).
