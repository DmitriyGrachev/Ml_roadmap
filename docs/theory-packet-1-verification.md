# Теория ядра — пакет 1: журнал проверки

Дата: 04.10.2026. Репозиторий `C:\ProjectsDirectory\AIML\_road`, ветка
`codex/ai-ml-wave1`, HEAD `836028944eceaa260cb47d0056b593af4a4648d4`.
Работа выполнена поверх существующего незакоммиченного Object Model pilot.
Среда проверки: Python 3.12.14, NumPy 2.5.3, uv 0.12.17. Новые зависимости,
модели и датасеты не устанавливались и не скачивались.

## Создано

- По одному `theory.md` для Collections, Functions, Typing и NumPy; README каждого
  урока ведёт в объяснение и существующую практику. Python-примеры сохранены.
- NumPy `walkthrough.py`, три SVG и пять тестов его фактического вывода.
- Четыре инфраструктурных doctest-проверки исполняют независимые `pycon`-блоки
  четырёх теоретических уроков. Это не новые student targets.
- В [существующей карте](wave2-coverage.md#theory-packet-1) отмечены пять видов
  свидетельств, исходные пробелы и порядок будущих редакционных пакетов PLANNED.

## Техническая проверка

Все команды выполнялись из корня репозитория в существующей среде, без sync:

| Команда | Фактический результат |
| --- | --- |
| `uv run --offline --no-sync pytest -q` | 936 passed, 39 skipped, 1160 xfailed; финальный повтор 83.60 s, exit 0 |
| `uv run --offline --no-sync ruff check .` | All checks passed, exit 0 |
| `uv run --offline --no-sync ruff format --check .` | 791 files already formatted, exit 0 |
| `uv run --offline --no-sync mypy` | No issues in 612 source files, exit 0 |
| Целевая проверка ниже | 86 passed, 1.83 s, exit 0 |
| `git diff --check` | Нет ошибок whitespace |

```powershell
uv run --offline --no-sync pytest tests/integration/test_theory_examples.py modules/03_data_foundations/tests/test_numpy_walkthrough.py modules/01_python_core/tests/test_learning_flow.py modules/01_python_core/tests/test_examples.py modules/03_data_foundations/tests/test_examples.py -q
```

В общем прогоне осталось одно предупреждение Starlette/AnyIO о deprecated
`BlockingPortal`. Существующие skip/xfail — не успешное выполнение ученических
заданий. Ничего не переведено в pass ослаблением tests или `check`.

Для walkthrough применён TDD: пять поведенческих тестов сначала упали из-за
отсутствующего файла, затем прошли после реализации. Проверяются формы, значения,
общая память, несовместимые формы и объёмы — не наличие терминов в тексте.
Отдельно выполнены **25 независимых pycon-блоков / 106 интерактивных шагов**:
Collections 20, Functions 19, Typing 16, NumPy 51.

Все пять файлов примеров запущены напрямую: три сохранённых Python example.py,
сохранённый NumPy example.py и новый walkthrough.py. Вывод совпал с разборами;
ошибок stderr не было. Для иллюстрации Typing отдельно проверен намеренно неверный
`names: list[str] = ["a"]; names.append(3)`: mypy сообщил несовместимый `int`
вместо `str`, ожидаемый exit 1. Этот одиночный фрагмент проверялся с
`--config-file NUL --strict --python-version 3.12 -c ...`, чтобы не совмещать `-c`
с проектным списком packages. Конфигурация проекта не изменена; полный mypy выше
выполнен с ней. Сообщение `NUL: No [mypy] section` относится только к этому
изолированному вызову, не к проверке проекта.

### Ссылки и отображение

Одноразовая утилита в игнорируемом `generated-reports/theory-packet-1/` использовала
уже доступные Mistune/BeautifulSoup: проверила 187 локальных ссылок на файлы,
изображения и якоря в десяти документах, alt,
12 уникальных внешних URL (HTTP 200 и указанные anchors), разобрала три SVG как XML
с title/description и без script. Это не новая зависимость учебного проекта.
Проверка воспроизводится командой
`uv run --offline --no-sync python generated-reports/theory-packet-1/verify_render.py`;
её проверка внешних ссылок требует сети, несмотря на offline-режим менеджера uv.

Во встроенном браузере просмотрен **локальный статический Markdown-render**:
теория NumPy, таблицы Collections/Functions/Typing и полные три SVG. Подписи,
стрелки, значения и последовательность мутаций сверены с кодом; текст SVG не
выходит за границы. После визуального обнаружения исправлено отображение union
в таблице Typing: `str | None` виден без служебного escaping. Проверялись также
раскрытие самопроверки и переход по локальной навигации.
GitHub/PyCharm-render и мобильный вид **не проверялись**; pixel-perfect совпадение
разных Markdown-просмотрщиков не заявляется. Веб-приложение не создавалось.

### Найденное и исправленное

- Первый общий прогон: 1 failed, 935 passed. Проверка ссылок поймала неверное имя
  папки Pandas и ссылку на ещё не созданный этот журнал. Путь исправлен на
  `02_pandas_core`, журнал создан, проверка ссылок и общий прогон повторены успешно.
- Ruff format нашёл пропущенную пустую строку в pycon-примере closure; исправлено.
- Визуальная проверка выявила сломанную Markdown-таблицу из-за `|` в union;
  отображение исправлено и повторно проверено в браузере.
- Независимое read-only ревью не нашло Critical/Important замечаний. Исправлены
  два Minor: точная формулировка аргумента-литерала в trace callback и границы
  AST-проверки циклов. Comprehensions/helper calls не объявлены автоматически
  исключёнными; векторизация обоих student-решений требует также ручной проверки.

### Сохранность

Перед работой сняты SHA-256 всех 813 существовавших non-ignored файлов. Из них
изменились **только пять** разрешённых документов: четыре README текущих уроков
и `docs/wave2-coverage.md`. Остальные 808 файлов сохранены байт-в-байт, включая
все ранее незакоммиченные файлы Object Model pilot. Добавлено 11 файлов пакета.
`curriculum.toml`, CLI, student implementations/TODO/tests, notebook, lockfile и
`pyproject.toml` не изменены. Все 162 ID и test/check targets прежние.
SHA-256 `progress.md` до и после:
`9C78D95D05EFB7234C8B3412D072577916A11192531AEE1B27A0DF60CE647DC0`.
HEAD прежний. Commit/push/merge не выполнялись.

## Файлы пакета

Новые (не считая сохранённого ранее пилота):

- [Collections theory](../modules/01_python_core/02_collections/theory.md)
- [Functions theory](../modules/01_python_core/03_functions/theory.md)
- [Typing theory](../modules/01_python_core/04_typing/theory.md)
- [NumPy theory](../modules/03_data_foundations/01_numpy/theory.md)
- [NumPy walkthrough](../modules/03_data_foundations/01_numpy/walkthrough.py)
- [axes.svg](../modules/03_data_foundations/01_numpy/assets/axes.svg)
- [broadcasting.svg](../modules/03_data_foundations/01_numpy/assets/broadcasting.svg)
- [views.svg](../modules/03_data_foundations/01_numpy/assets/views.svg)
- [Walkthrough tests](../modules/03_data_foundations/tests/test_numpy_walkthrough.py)
- [Executable theory tests](../tests/integration/test_theory_examples.py)
- Этот журнал: `docs/theory-packet-1-verification.md`.

Изменены: README этих четырёх уроков и существующая `docs/wave2-coverage.md`.
Архитектура: README остаётся входом и списком заданий; theory — подробным
объяснением; пример — исполняемым доказательством; tests вне lesson targets —
проверкой корректности teacher-материалов. Нет нового слоя CLI/регистрации.

## Что проверяет ученик

Самостоятельные TODO, отчёты и progress не заполняются. Прогноз результата,
объяснение причины ошибки, перенос на новую вариацию и оценка памяти требуют
вашей попытки и человеческой проверки. Это не подтверждается teacher-тестами.

## Начало

После Object Model откройте [Collections](../modules/01_python_core/02_collections/README.md),
затем Functions и Typing в прежнем порядке. В NumPy начните с
[README](../modules/03_data_foundations/01_numpy/README.md) и проходите теорию за
три подхода: §1–3, §4–5, §6–9. Команды даны в уроках относительно корня проекта.

```powershell
Set-Location C:\ProjectsDirectory\AIML\_road
uv run --offline --no-sync python modules/01_python_core/02_collections/example.py
```

Прочитайте ситуацию → запишите прогноз → разберите объяснение и выполните пример
→ сделайте самостоятельную вариацию → решите существующее упражнение → запустите
его `test` и строгий `check`. Для NumPy:

```powershell
uv run --offline --no-sync python modules/03_data_foundations/01_numpy/walkthrough.py
```

После **своей** реализации, например:

```powershell
uv run --offline --no-sync python scripts/learn.py test data-payment-matrix
uv run --offline --no-sync python scripts/learn.py check data-payment-matrix
```

Эти команды `check` приведены как следующий шаг ученика, не как утверждение,
что незавершённые задания были зачтены при подготовке материалов.
