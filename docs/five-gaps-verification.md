# Пять учебных дополнений: что готово и откуда начинать

Дата: 28.10.2026. Существующий `DmitriyGrachev/Ml_roadmap`, ветка
`codex/ai-ml-wave1`. Это дополнение прежних уроков, не новый курс.
Теория, завершённые учительские демонстрации и отдельная практика подготовлены
по всем пяти направлениям. Ученические решения/отчёты/progress не заполнены.
**Реальный PostgreSQL и контейнерный запуск пока NOT_RUN**: среды отсутствуют.

## Начало с нуля

Первым откройте [Environment](../modules/01_python_core/00_environment/README.md),
выполните настройку из него, затем [Первые строки Python](../modules/01_python_core/00_environment/basics.md).
Из корня `C:/ProjectsDirectory/AIML/_road`:

```powershell
uv sync --locked
uv run python modules/01_python_core/00_environment/basics_demo.py
uv run pytest modules/01_python_core/tests/test_basics_demo.py -q
Get-Content modules/01_python_core/00_environment/practice/README.md
uv run python scripts/learn.py test python-control-flow
```

Первая команда чтения открывает текст задания; меняйте только **свой** `starter.py`.
После собственной реализации:

```powershell
uv run python scripts/learn.py check python-control-flow
```

`test` допускает незавершённые TODO как xfail; строгий `check` выбранного target
не засчитывает обязательные xfail/skip. Ни одна команда не отмечает progress за вас.
Потом — прежние Object Model → Collections → Functions → Typing и дальше по roadmap.
Не начинайте одновременно с пяти дополнений: поздним темам нужны prerequisites.

## Где теория, наглядность и самостоятельная работа

| Тема | Объяснение и разобранный пример | Визуальная опора | Самостоятельный target / критерий понимания | Место |
| --- | --- | --- | --- | --- |
| Python с нуля | [basics.md](../modules/01_python_core/00_environment/basics.md), [basics_demo.py](../modules/01_python_core/00_environment/basics_demo.py) | ветки обработки строки, trace накопителя/while, вызов→return | [`python-control-flow`](../modules/01_python_core/00_environment/practice/README.md): написать свой счётчик; объяснить границы, состояние и остановку | после Environment до Object Model |
| Статистический дизайн | [experiment_design.md](../modules/03_data_foundations/04_practical_statistics/experiment_design.md), [experiment_demo.py](../modules/03_data_foundations/04_practical_statistics/experiment_demo.py) | ручной SE/n, таблицы A/A–A/B, fixed horizon/peeking и multiplicity | [`data-experiment-design`](../modules/03_data_foundations/exercises/experiment_design/README.md): Bonferroni TODO + собственный prereg experiment; интерпретация REVIEW | после прежних Bayes, paired comparison и randomized experiment, с их ML prerequisites |
| Представления и аномалии | [representations.md](../modules/04_machine_learning/04_models/representations.md), [representations.py](../modules/04_machine_learning/04_models/representations.py) | две метрики расстояния, таблица shapes/projections/centres/anomaly scores | [`ml-representation-study`](../modules/04_machine_learning/exercises/representation_study/README.md): inverse-map TODO + свои сенсоры; cluster≠class, unusual≠invalid | после NumPy, preprocessing/validation/models |
| Fairness и bias | [bias.md](../modules/04_machine_learning/05_evaluation/bias.md), [bias_slices.py](../modules/04_machine_learning/05_evaluation/bias_slices.py) | confusion tables и [состав выборки SVG](../modules/04_machine_learning/05_evaluation/bias_composition.svg) | [`ml-bias-slices`](../modules/04_machine_learning/exercises/bias_slices/README.md): grouped counts/rates + свой разбор; empty denominator=None, не причинный вывод из метрик | после metrics/threshold/calibration |
| SQL и контейнер | [SQL](../modules/02_python_backend/07_postgresql/sql_basics.md), [SQLite demo](../modules/02_python_backend/07_postgresql/sql_basics_demo.py), [container practice](../modules/02_python_backend/09_docker_delivery/container_practice.md) | вход→filter/group/join/window→строки; image→process→port/mount→reload | [`backend-sql-foundations`](../modules/02_python_backend/exercises/sql_foundations/README.md): latest-valid SQL; container done требует настоящего build/HTTP/restart/recreate | SQL после Python/data; container после backend и готового CPU API |

Во всех пяти — интуиция, точные определения с English terms, разбор по шагам,
типичная ошибка, прогноз и другая самостоятельная задача. Вопросы и свои
исследования требуют объяснения учеником; готовый demo не является ответом за него.
Статистическая демонстрация ограничена независимыми normal observations с known sigma;
она не обещает достоверность произвольного A/B. SVM/NB остаются OPTIONAL и не реализованы.

## Команды демонстраций

Следующие команды CPU/offline, модели/датасеты не скачивают:

```powershell
uv run python modules/01_python_core/00_environment/basics_demo.py
uv run python modules/03_data_foundations/04_practical_statistics/experiment_demo.py
uv run python modules/04_machine_learning/04_models/representations.py
uv run python modules/04_machine_learning/05_evaluation/bias_slices.py
uv run python -m modules.02_python_backend.07_postgresql.sql_basics_demo
```

Пакеты используют stdlib и прежние NumPy/scikit-learn. Новых зависимостей нет.
Matplotlib не требуется для обязательных примеров; никаких notebook/widgets/web app.
Полностью готовые teacher functions отделены от student TODO.

## Проверки автора

Здесь фиксируются фактические результаты текущей итерации. Основное проверочное окружение — существующее
`.venv-base-check/Scripts/python.exe`, Python 3.12.14 / SQLite 3.53.1.

- Python teacher: RED10 → GREEN10; SQL teacher: RED5 → GREEN5.
- Statistics: RED25 → GREEN, финально 27 tests; отдельный tiny-alpha regression
  исправляет потерю точности в power через устойчивые normal tails.
- Representations: RED10 → GREEN10, реальные sklearn fit только на train.
- Bias: RED14 → GREEN14, confusion/rates и состав выборки совпадают с таблицами/SVG.
- Новые student targets остаются TODO. Их tests работают через прежний exercise_call;
  инфраструктурный xfail не считается зачётом. SQL нулевое значение проверяется
  отдельным dataset, где именно ноль должен попасть в результат.
- Каталог: добавлено **пять exercise ID** к прежним 163; прежние IDs/targets/order
  сохранены. Student tests вынесены из старых широких lesson directories.
- Визуально проверен raster preview настоящего `bias_composition.svg`: текст/блоки/оси
  читаемы, 8/12 и 12/20 соответствуют коду. Rasterizer — существующий bundled Sharp,
  в зависимости проекта он не добавлялся. Остальные визуальные опоры — Markdown
  tables/text diagrams, согласованные с выполненным кодом; отдельный browser-render
  всего Markdown не выполнялся.

Реальный Docker/PostgreSQL недоступен. SQLite, ASGI unit tests, чтение Dockerfile и
подготовленные команды **не подменяют** container/PostgreSQL integration.
Hosted CI, cloud, vLLM и общий benchmark качества не запускались этой итерацией.
vLLM по-прежнему DEFERRED_ENV. Открытые ученические эксперименты не объявлены успешными.

## Файлы и архитектурные решения

Новые материалы расположены рядом с существующими уроками; README остаются входами.
Добавлены `basics*`, `experiment*`, `representations*`, `bias*`, `sql_basics*`,
`container_practice.md` и тесты соответствующих демонстраций. У пяти новых заданий
свои README/starter/tests; offline guards проверяются инфраструктурными tests.
Общая регистрация только в `curriculum.toml`, карта в
[wave2-coverage](wave2-coverage.md#coverage-gaps-20261028); CLI-код не менялся.

Работа выполнена в прежней dirty ветке, без worktree/reset/commit/push/merge:
перенос от HEAD потерял бы существующие незакоммиченные материалы. Независимые
подтемы разрабатывались в непересекающихся папках, общий catalog/roadmap обновлял
основной исполнитель. Полная SHA-карта исходных 1048 файлов сохранена в ignored
author artifacts для проверки пользовательских реализаций/progress/dependencies.

## Итоговые фактические результаты

Все команды из корня, Python — `.venv-base-check/Scripts/python.exe`:

| Команда / проверка | Результат |
| --- | --- |
| `-m pytest -q` | **1477 passed, 78 skipped, 1209 xfailed**, 122.62 s, exit 0 |
| `-m ruff check .` | PASS |
| `-m ruff format --check .` | **1036 files**, PASS |
| `-m mypy` | **716 source files**, PASS |
| Пять teacher demo commands выше | все exit 0, вывод сохранён; работают offline |
| `scripts/learn.py test <new-id>` для всех пяти | каждый exit 0; TODO не зачтены |
| `scripts/learn.py check <new-id>` для всех пяти | каждый exit 1 с CHECK INCOMPLETE — ожидаемый отказ до реализации |
| Все Markdown local paths, включая untracked | **341 document / 2170 links**, проблем нет |
| Anchors в 24 затронутых Markdown documents | **32 anchors**, проблем нет |
| `git diff --check` | PASS |
| `uv sync --locked --offline --dry-run` | exit 0, только план переустановки локального project package; install/download не выполнялись |

Полный pytest имеет один прежний Starlette/AnyIO deprecation warning. Skip относятся
к optional средам; xfail относятся к незавершённым заданиям и не являются credit.
Первая полная попытка выявила две пропущенные записи в author inventories:
`test_every_cataloged_exercise_has_a_boundary_or_intentional_input` и
`test_every_backend_starter_imports_under_a_collision_safe_name`. Добавлены точные
пять новых TODO boundaries и путь нового SQL starter, проверки не ослаблялись.
Обе сначала воспроизведены красными, затем прошли; итоговый полный запуск зелёный.
Проверка реальной CLI также выявила несуществующую `show` в черновике инструкции:
заменена на `Get-Content`; CLI не расширялся ради документации.

Числа незавершённых новых cases: Python12, statistics13, representations13,
bias4 (его validation cases уже предоставлены), SQL5. Они по-прежнему вызывают
`NotImplementedError` на требуемых student boundaries.

Полная SHA-сверка с baseline1048 подтверждает: старые student implementations/reports,
progress, `src/` CLI, `pyproject.toml`, `uv.lock` не изменены. Префикс каталога до
пяти новых записей совпадает с исходным SHA256: старые163 items сохранены точно.
HEAD прежний: `836028944eceaa260cb47d0056b593af4a4648d4`. Commit/push/merge не выполнялись.
Author logs, baseline/changes и непубличные технические отчёты сохранены в ignored
`artifacts/five-gaps-work/`; их не надо переносить в ученический report.

## Полный список новых файлов

- [docs/five-gaps-verification.md](../docs/five-gaps-verification.md)
- [docs/superpowers/plans/2026-10-28-five-gaps.md](../docs/superpowers/plans/2026-10-28-five-gaps.md)
- [modules/01_python_core/00_environment/basics.md](../modules/01_python_core/00_environment/basics.md)
- [modules/01_python_core/00_environment/basics_demo.py](../modules/01_python_core/00_environment/basics_demo.py)
- [modules/01_python_core/00_environment/practice/README.md](../modules/01_python_core/00_environment/practice/README.md)
- [modules/01_python_core/00_environment/practice/__init__.py](../modules/01_python_core/00_environment/practice/__init__.py)
- [modules/01_python_core/00_environment/practice/conftest.py](../modules/01_python_core/00_environment/practice/conftest.py)
- [modules/01_python_core/00_environment/practice/starter.py](../modules/01_python_core/00_environment/practice/starter.py)
- [modules/01_python_core/00_environment/practice/test_starter.py](../modules/01_python_core/00_environment/practice/test_starter.py)
- [modules/01_python_core/tests/test_basics_demo.py](../modules/01_python_core/tests/test_basics_demo.py)
- [modules/02_python_backend/07_postgresql/sql_basics.md](../modules/02_python_backend/07_postgresql/sql_basics.md)
- [modules/02_python_backend/07_postgresql/sql_basics_demo.py](../modules/02_python_backend/07_postgresql/sql_basics_demo.py)
- [modules/02_python_backend/09_docker_delivery/container_practice.md](../modules/02_python_backend/09_docker_delivery/container_practice.md)
- [modules/02_python_backend/exercises/sql_foundations/README.md](../modules/02_python_backend/exercises/sql_foundations/README.md)
- [modules/02_python_backend/exercises/sql_foundations/__init__.py](../modules/02_python_backend/exercises/sql_foundations/__init__.py)
- [modules/02_python_backend/exercises/sql_foundations/conftest.py](../modules/02_python_backend/exercises/sql_foundations/conftest.py)
- [modules/02_python_backend/exercises/sql_foundations/starter.py](../modules/02_python_backend/exercises/sql_foundations/starter.py)
- [modules/02_python_backend/exercises/sql_foundations/test_starter.py](../modules/02_python_backend/exercises/sql_foundations/test_starter.py)
- [modules/02_python_backend/tests/test_sql_basics_demo.py](../modules/02_python_backend/tests/test_sql_basics_demo.py)
- [modules/03_data_foundations/04_practical_statistics/experiment_demo.py](../modules/03_data_foundations/04_practical_statistics/experiment_demo.py)
- [modules/03_data_foundations/04_practical_statistics/experiment_design.md](../modules/03_data_foundations/04_practical_statistics/experiment_design.md)
- [modules/03_data_foundations/exercises/experiment_design/README.md](../modules/03_data_foundations/exercises/experiment_design/README.md)
- [modules/03_data_foundations/exercises/experiment_design/__init__.py](../modules/03_data_foundations/exercises/experiment_design/__init__.py)
- [modules/03_data_foundations/exercises/experiment_design/conftest.py](../modules/03_data_foundations/exercises/experiment_design/conftest.py)
- [modules/03_data_foundations/exercises/experiment_design/report-template.md](../modules/03_data_foundations/exercises/experiment_design/report-template.md)
- [modules/03_data_foundations/exercises/experiment_design/starter.py](../modules/03_data_foundations/exercises/experiment_design/starter.py)
- [modules/03_data_foundations/exercises/experiment_design/test_starter.py](../modules/03_data_foundations/exercises/experiment_design/test_starter.py)
- [modules/03_data_foundations/tests/test_experiment_design.py](../modules/03_data_foundations/tests/test_experiment_design.py)
- [modules/04_machine_learning/04_models/representations.md](../modules/04_machine_learning/04_models/representations.md)
- [modules/04_machine_learning/04_models/representations.py](../modules/04_machine_learning/04_models/representations.py)
- [modules/04_machine_learning/05_evaluation/bias.md](../modules/04_machine_learning/05_evaluation/bias.md)
- [modules/04_machine_learning/05_evaluation/bias_composition.svg](../modules/04_machine_learning/05_evaluation/bias_composition.svg)
- [modules/04_machine_learning/05_evaluation/bias_slices.py](../modules/04_machine_learning/05_evaluation/bias_slices.py)
- [modules/04_machine_learning/05_evaluation/test_bias_slices.py](../modules/04_machine_learning/05_evaluation/test_bias_slices.py)
- [modules/04_machine_learning/exercises/bias_slices/README.md](../modules/04_machine_learning/exercises/bias_slices/README.md)
- [modules/04_machine_learning/exercises/bias_slices/conftest.py](../modules/04_machine_learning/exercises/bias_slices/conftest.py)
- [modules/04_machine_learning/exercises/bias_slices/starter.py](../modules/04_machine_learning/exercises/bias_slices/starter.py)
- [modules/04_machine_learning/exercises/bias_slices/test_starter.py](../modules/04_machine_learning/exercises/bias_slices/test_starter.py)
- [modules/04_machine_learning/exercises/representation_study/README.md](../modules/04_machine_learning/exercises/representation_study/README.md)
- [modules/04_machine_learning/exercises/representation_study/conftest.py](../modules/04_machine_learning/exercises/representation_study/conftest.py)
- [modules/04_machine_learning/exercises/representation_study/report.md](../modules/04_machine_learning/exercises/representation_study/report.md)
- [modules/04_machine_learning/exercises/representation_study/starter.py](../modules/04_machine_learning/exercises/representation_study/starter.py)
- [modules/04_machine_learning/exercises/representation_study/test_starter.py](../modules/04_machine_learning/exercises/representation_study/test_starter.py)
- [modules/04_machine_learning/tests/test_representations.py](../modules/04_machine_learning/tests/test_representations.py)

Существующие файлы, изменённые в этой итерации:

- [docs/local-generator-verification.md](../docs/local-generator-verification.md)
- [curriculum.toml](../curriculum.toml)
- [docs/roadmap.md](../docs/roadmap.md)
- [docs/wave2-coverage.md](../docs/wave2-coverage.md)
- [modules/01_python_core/00_environment/README.md](../modules/01_python_core/00_environment/README.md)
- [modules/02_python_backend/07_postgresql/README.md](../modules/02_python_backend/07_postgresql/README.md)
- [modules/02_python_backend/09_docker_delivery/README.md](../modules/02_python_backend/09_docker_delivery/README.md)
- [modules/02_python_backend/tests/test_lesson_contracts.py](../modules/02_python_backend/tests/test_lesson_contracts.py)
- [modules/03_data_foundations/04_practical_statistics/README.md](../modules/03_data_foundations/04_practical_statistics/README.md)
- [modules/04_machine_learning/04_models/README.md](../modules/04_machine_learning/04_models/README.md)
- [modules/04_machine_learning/05_evaluation/README.md](../modules/04_machine_learning/05_evaluation/README.md)
- [tests/integration/test_catalog_contracts.py](../tests/integration/test_catalog_contracts.py)
- [tests/integration/test_repository_hygiene.py](../tests/integration/test_repository_hygiene.py)
