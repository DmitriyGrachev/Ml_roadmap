# R02 Backend и SQL: материалы и проверка

11.10.2026. Четыре небольших дополнения к существующим урокам готовы для чтения.
Это готовность авторских материалов, не выполненные ученические задания.

## Порядок работы

1. После FastAPI/typing — [field validator и HTTP-ошибка](../modules/02_python_backend/02_pydantic/theory.md),
   затем прежний `backend-transaction-contract`.
2. После SQLAlchemy basics — [flush, commit, rollback и close](../modules/02_python_backend/06_sqlalchemy/theory.md),
   затем прежний `backend-transaction-repository`.
3. После Python tests/DI — [yield-fixture и очистка при ошибке](../modules/02_python_backend/08_api_integration_testing/theory.md),
   затем прежний `backend-api-test-review`.
4. После SQL — [query plan и один индекс](../modules/02_python_backend/exercises/analytics_sql/plan_theory.md),
   самостоятельная вариация рядом с `backend-analytics-sql`.

В каждом разборе: прогноз → механизм → запускаемый другой пример → ошибка →
вариация и вопросы. Никакой Transaction/repository/review TODO не решён.
Имеющиеся ID, targets и progress не изменены.

## Реальные проверки

Windows, Python 3.12.14, FastAPI 0.141.1, Pydantic 2.13.5,
SQLAlchemy 2.0.54, Starlette 1.6.0, SQLite 3.53.1. Использованы существующие пакеты,
без установки. Команды из корня:

```powershell
uv run --no-sync pytest modules/02_python_backend/tests/test_r02_boundaries.py modules/02_python_backend/tests/test_lesson_contracts.py -q
uv run --no-sync python modules/02_python_backend/02_pydantic/walkthrough.py
uv run --no-sync python modules/02_python_backend/06_sqlalchemy/walkthrough.py
uv run --no-sync python modules/02_python_backend/08_api_integration_testing/walkthrough.py
uv run --no-sync python modules/02_python_backend/exercises/analytics_sql/plan_demo.py
```

**16 passed**, exit 0: 11 новых случаев и пять прежних контрактов уроков.
Все четыре примера завершились exit 0. Независимый reviewer повторил эти проверки
и сверил вывод с объяснением. Единственное предупреждение — прежний deprecated
alias `anyio.abc.BlockingPortal` внутри установленного Starlette.

Проверены реальные HTTP-ответы/эффекты, сохранённые SQLite-строки, rollback/close,
следующая рабочая сессия, независимость app и очистка fixture после настоящего
падающего теста во временной папке. Эта дочерняя проба намеренно получает
`1 failed, 1 passed`; основной тест проверяет именно этот результат.

SQL: одинаковые 20 упорядоченных строк до/после индекса; наблюдались SCAN и SEARCH,
семь warm-замеров каждой фазы, +60 выделенных страниц по 4096 байт. Время зависит
от запуска; тест не требует ускорения. PostgreSQL, cold-disk и конкурентная
нагрузка не проверялись.

```powershell
uv run --no-sync ruff check modules/02_python_backend/02_pydantic/walkthrough.py modules/02_python_backend/06_sqlalchemy/walkthrough.py modules/02_python_backend/08_api_integration_testing/walkthrough.py modules/02_python_backend/exercises/analytics_sql/plan_demo.py modules/02_python_backend/tests/test_r02_boundaries.py
uv run --no-sync ruff format --check modules/02_python_backend/02_pydantic/walkthrough.py modules/02_python_backend/06_sqlalchemy/walkthrough.py modules/02_python_backend/08_api_integration_testing/walkthrough.py modules/02_python_backend/exercises/analytics_sql/plan_demo.py modules/02_python_backend/tests/test_r02_boundaries.py
uv run --no-sync mypy --follow-imports=silent -m modules.02_python_backend.02_pydantic.walkthrough -m modules.02_python_backend.06_sqlalchemy.walkthrough -m modules.02_python_backend.08_api_integration_testing.walkthrough -m modules.02_python_backend.exercises.analytics_sql.plan_demo -m modules.02_python_backend.tests.test_r02_boundaries
```

Ruff — без замечаний; format — пять файлов; mypy — пять source files без ошибок.
Четыре Python-фрагмента в Markdown проверены отдельно как выдержки, 28 локальных
ссылок разрешаются. Официальные источники приведены в уроках и просмотрены.
В локальном Mistune-просмотре проверены основные схемы/таблицы всех четырёх теорий
при ширине около 1280 px. Это не проверка всех редакторов или мобильных экранов.

Полная регрессия всего дополняемого маршрута выполняется после интеграции остальных
пакетов; перечисленные узкие проверки её не заменяют. Независимое review R02:
**Approved**, открытых замечаний нет. Понимание, вариации и защита ученика —
**REQUIRES_REVIEW**.
