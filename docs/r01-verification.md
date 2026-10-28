# R01: подготовленные материалы и реальные проверки

Дата: **11.10.2026**. Репозиторий `C:/ProjectsDirectory/AIML/_road`, ветка
`codex/ai-ml-wave1`, HEAD `836028944eceaa260cb47d0056b593af4a4648d4` не изменён.
Среда: Windows, существующая `.venv`, Python **3.12.14**. Установок не было.

Подготовлен только R01 из [согласованного плана](superpowers/plans/2026-10-11-remaining-roadmap.md#r01).
Готовность материалов — **READY**; самостоятельность ученика — **REQUIRES_REVIEW**.
R02–R12 остаются PLANNED. Модели, GPU, vLLM, облачные сервисы не запускались.

## С чего начать этот пакет

Это дополнение к Python Core, не новый стартовый курс. Сначала нужны прежние
Object Model, Functions и Typing. В соответствующем месте маршрута:

1. Открыть [05_data_modeling/README.md](../modules/01_python_core/05_data_modeling/README.md)
   → theory.md → прогнозы → walkthrough → собственная вариация и payment_model.
2. Затем [06_exceptions_io/README.md](../modules/01_python_core/06_exceptions_io/README.md):
   предсказать состояние файлов по фазам, запустить demo, перейти к json_export.
3. Затем [09_testing/README.md](../modules/01_python_core/09_testing/README.md):
   вывести случаи из контракта preview, прочитать реальный traceback, разобрать композицию.
4. Выполнить [document outline](../modules/01_python_core/09_testing/practice/document_outline/README.md):
   написать собственные тесты, реализовать v1, изменить требование до v2, проверить
   дефектный AI-кандидат теми же независимыми случаями и объяснить контрпримеры.

Из корня проекта, в уже подготовленном окружении:

```powershell
uv run --no-sync python modules/01_python_core/05_data_modeling/walkthrough.py
uv run --no-sync python modules/01_python_core/06_exceptions_io/walkthrough.py
uv run --no-sync python modules/01_python_core/09_testing/walkthrough.py
uv run --no-sync pytest modules/01_python_core/09_testing/walkthrough.py -q
```

Три demo-команды завершаются с кодом 0. Четвёртая запускает девять **учительских**
примеров тестов; это не зачёт вашей работы. Перед каждым запуском запишите прогноз.

```powershell
uv run --no-sync python modules/01_python_core/09_testing/debugging/empty_preview/broken.py
uv run --no-sync pytest modules/01_python_core/09_testing/practice/document_outline/outline_cases.py -q
```

Первая команда намеренно возвращает **1** с реальными frames и IndexError.
Вторая до написания тестов возвращает **5: no tests ran**, не PASS. Файлы
`outline_cases.py` и `review.md` оставлены пустыми, starter не реализован.
После самостоятельной работы оцениваются выбор случаев, RED/GREEN, изменение
требования и объяснение дефекта. Один зелёный запуск не доказывает полноту тестов.
Новый ID не создавался; старый смысл `test`/`check <ID>` не изменён. Имя
`outline_cases.py` намеренно не соответствует маске автопоиска pytest: собственные
тесты этой ручной практики запускаются **только явным путём** и не расширяют
прежний lesson-target `python-testing`. Тестовые функции внутри называйте `test_...`.

## Что добавлено и почему

В каждом из трёх существующих уроков добавлены `theory.md` и `walkthrough.py`;
README получил вход и порядок работы. Русская теория содержит английские термины,
прогнозы, разбор значений, таблицы/схему состояний, типичные ошибки и вопросы.

- `05_data_modeling`: PageSpan с инвариантом; отдельные finite Decimal/ASCII пробы.
  Это не готовая Payment-модель с переименованными полями.
- `06_exceptions_io`: отдельные фазы проблемной сериализации каталога и публикации
  фиксированного текстового объявления. Нет общего JSON exporter для student TODO.
  Объяснены ownership, close-before-replace, cleanup failure, исходное исключение
  и различие атомарной видимости и долговечности после аварии.
- `09_testing`: usable preview, его тесты и отдельный intentional failure;
  полная композиция подсчёта слов по абзацам не решает самостоятельный outline.
  Старые Functions/mutable_defaults/stateful_report переиспользованы ссылками.

Полный список новых учебных/проверочных файлов:

```text
modules/01_python_core/
  05_data_modeling/{theory.md, walkthrough.py}
  06_exceptions_io/{theory.md, walkthrough.py}
  09_testing/{theory.md, walkthrough.py}
  09_testing/debugging/empty_preview/broken.py
  09_testing/practice/document_outline/
    README.md, __init__.py, starter.py, candidate.py, outline_cases.py, review.md
  tests/test_r01_value_objects.py
  tests/test_r01_atomic_phases.py
  tests/test_r01_test_design.py
docs/r01-verification.md
```

Из существующих файлов изменены только три README этих уроков и четыре документа
навигации: roadmap, ai-ml-extension-plan, wave2-coverage и общий remaining-roadmap plan.
Старые примеры, упражнения, реализации, progress, curriculum, CLI, зависимости и lock
не менялись. Демо запускаются локально, не требуют RTX 5060 или дополнительного ПО.

## Технические проверки

Авторские behavior tests сначала получили RED на API-stubs: **33 failed**, без
setup errors; после реализации — **33 passed**. Предварительная попытка до появления
самих новых файлов дала 1 failed / 32 setup errors и не считалась проверкой поведения.

Ниже реальные команды из корня, не обещания будущих проверок:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m pytest modules/01_python_core/tests modules/01_python_core/09_testing/walkthrough.py -q
uv run --no-sync pytest modules/01_python_core/tests/test_r01_value_objects.py modules/01_python_core/tests/test_r01_atomic_phases.py modules/01_python_core/tests/test_r01_test_design.py modules/01_python_core/09_testing/walkthrough.py -q
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy
```

| Проверка | Фактический результат |
| --- | --- |
| Полный baseline до R01 | 1022 passed, 50 skipped, 1160 xfailed, 1 warning; exit 0 |
| Полный regression, включая collection-fix | **1056 passed, 50 skipped, 1160 xfailed**, 1 warning, 128.37 s; exit 0 |
| Python Core author regression + embedded teacher suite, после collection-fix | **107 passed**; exit 0 |
| Только новые author + embedded teacher cases, после collection-fix | **43 passed**; exit 0 |
| Ruff | All checks passed; exit 0 |
| Форматирование | Пропуски пустых строк в Python-fence исправлены; **877 files already formatted**, exit 0 |
| mypy по конфигурации проекта | **644 source files**, no issues; exit 0 |

Итоговый пакет содержит 34 автоматически собираемых авторских теста; они объясняют
прирост полного regression относительно baseline. Первый общий запуск до collection-fix
дал 1055 passed; после исправления полный suite запущен заново, результат в таблице.
Девять embedded teacher cases из walkthrough запускаются явно и не удваиваются
в обычном автопоиске. Старые xfail/skip не превращались в подтверждение освоения.

При интеграционной проверке выявлена и устранена граница автосбора: прежний
`python-testing` запускает всю папку урока. Первоначальное имя `test_outline.py`
привело бы к скрытому расширению зачёта после написания учеником тестов. Новый
behavioral regression копирует урок во временную папку и добавляет намеренно
падающий тест **только в копию**. До исправления проверка дала **1 failed**;
после переименования нового пустого файла в `outline_cases.py` — **1 passed**:
явный путь обнаруживает настоящую ошибку, а directory-target её не собирает.
Реальный ученический файл не заполнялся. Его нужно сохранить с указанным именем;
самостоятельно добавленный `test_*.py` снова подпадёт под обычный автопоиск.

Единственное предупреждение было и в baseline: Starlette TestClient использует
устаревающий alias `anyio.abc.BlockingPortal`. Зависимости ради его устранения
не менялись. Отдельные mypy-команды для новых walkthrough и debugging/practice
также прошли; попытка передать несколько одноимённых walkthrough напрямую одним
вызовом mypy дала duplicate module name, поэтому они проверены по отдельности.

## Примеры, ссылки и отображение

- Три фактических stdout полностью сопоставлены с `text`-блоками соответствующей
  теории; намеренный traceback также совпал с результатом `traceback.extract_tb`.
- Failure tests проверяют реальные bytes, нетронутый чужой файл, удаление только
  своего draft, идентичность первичной ошибки и отдельный отказ cleanup.
- Разовая проверка использует существующий `broken_local_links` не только для
  tracked, но и для новых untracked Markdown; якоря отдельно сопоставлены с
  явными ID и разобранными заголовками: **274 документа, 0 broken**, **40 якорей
  в 12 документах**. После обновления навигации команда
  `.venv/Scripts/python.exe -m pytest tests/integration/test_markdown_links.py tests/tooling/test_documentation.py -q`
  дала **13 passed**, exit 0. Разовый локальный QA-вызов:
  `.venv/Scripts/python.exe .superpowers/sdd/2026-10-11-remaining-roadmap/verify_materials.py`
  (служебный файл текущей сессии, не часть учебного интерфейса).
- **15 официальных внешних URLs** дали HTTP 200; все указанные fragment IDs найдены.
  Основные объяснения сверены с Python 3.12 и pytest documentation; это не копирование
  чужих упражнений. Конкретные разделы/границы чтения указаны в каждой теории.
- В локальном Mistune-предпросмотре браузера визуально просмотрены вводный разбор
  value object, таблица фаз I/O и матрица тестовых случаев. Русский текст, таблицы
  и code blocks читаются при ширине 1280 px; у просмотренных страниц нет общей
  горизонтальной прокрутки. Это не проверка каждой строки во всех Markdown-редакторах.
  Отдельного приложения для курса не добавлено; временный preview служил только QA.

## Что ещё не доказано

Технический PASS демонстраций не доказывает умение ученика выбрать тесты, перенести
инвариант, объяснить traceback или самостоятельно составить безопасный exporter.
Его реализации и отчёты не заполнены; содержательная защита нужна после его работы.
Training install/GPU/model evaluation, vLLM/Linux, CI/cloud в R01 не требовались и
не проводились. Это не свидетельство готовности будущих R02–R12.

Независимый task review: **Approved**, замечаний не найдено; отдельно проверено,
что демонстрации не реализуют старые Payment/JSON-export контракты.
После обнаружения границы автосбора проведён отдельный scoped re-review исправления:
**Approved for safe handoff**, новых замечаний нет; его условие полного regression выполнено.
SHA-256 сверка 903 исходных tracked/untracked файлов: **896 побайтно сохранены**,
семь изменённых документов перечислены выше; **17 новых файлов**, прежних удалённых нет.
`git diff --check` завершился с кодом 0. Служебный журнал оставлен локально, поскольку
история Git в этой итерации не обновлялась.
Commit/push/merge не выполнялись.
