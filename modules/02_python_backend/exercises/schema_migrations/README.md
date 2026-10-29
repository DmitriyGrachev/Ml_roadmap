# Alembic: заполненная база, backfill и возврат схемы

Catalog ID: `backend-schema-migrations`.

Предпосылки: SQL, транзакции, SQLAlchemy engine,
[теория миграций](theory.md). Цель: выполнить переход на существующих строках,
проверить новые ограничения и сохранить исходные данные при downgrade.

## Авторский SQLite demo

[demo_migrations/versions](demo_migrations/versions/0001_prediction_jobs.py)
содержит настоящие Alembic revisions, а не примеры SQL вне истории.
[demo.py](demo.py) создаёт временный файл, применяет `0001`, добавляет две строки,
переходит к `0002`, печатает данные, возвращается к `0001`. В репозиторий БД не пишется.

```bash
uv sync --group migrations
uv run --offline --group migrations python -m modules.02_python_backend.exercises.schema_migrations.demo
uv run --offline --group migrations pytest modules/02_python_backend/exercises/schema_migrations/test_demo.py -q
```

После upgrade у строк с 1250 и 0 milliseconds появляются 1.25 и 0.0 seconds.
После downgrade строки и исходные milliseconds остаются. Tests дополнительно
проверяют Unicode в имени, дробную секунду, новый INSERT, `NOT NULL`, позицию
`alembic_version`, повторный upgrade, отказ на испорченных legacy-данных до DDL
и rollback после искусственной ошибки, следующей за реальным `ADD COLUMN`.
Прохождение этих tests доказывает author example, а не выполнение задания ученика.

## Самостоятельный перенос: документы

В [student_migrations](student_migrations/versions/0001_documents.py) задана
исходная схема `documents(id,title,body)` с индексом `ix_documents_title`.
Тесты **сначала** применяют её и вставляют строки с пустым body, Unicode и переводом
строки. Не заменяйте эту фикстуру пустой базой.

Заполните `upgrade_database` и `downgrade_database` в [starter.py](starter.py):
они запускают Alembic для **student_migrations** на переданном файле SQLite.
Вспомогательный `demo.config_for(url, "student_migrations")` разрешён как
инфраструктура; выполнение author latency revisions не решает упражнение.
Реализуйте также `upgrade` и `downgrade` в
[0002_body_length.py](student_migrations/versions/0002_body_length.py).

Контракт новой версии: `body_length` — `INTEGER NOT NULL`, `CHECK >= 0`, равен
числу Unicode code points в старом `body`. `"ёж🙂"` имеет длину 3, а не количество
байтов UTF-8; пустая строка имеет длину 0. Сохраните исходные значения полей, ID и
title-index. После upgrade новые writers передают длину явно. Контракт не обещает
автоматического пересчёта при UPDATE body: объясните это ограничение на защите.
Downgrade удаляет только производную колонку и её ограничение. Повторный вызов
текущего Alembic target безопасен, а upgrade после downgrade повторяет backfill.

```bash
uv run --offline --group migrations pytest modules/02_python_backend/exercises/schema_migrations/test_starter.py -q
uv run --offline --group migrations python -m roadmap_tools.cli check backend-schema-migrations
```

Все четыре learner boundary намеренно `NotImplementedError`. Без optional group
модули тестов явно пропускаются с командой установки; strict check не даёт за skip
или xfail зачёт. Файлы migration version — часть задания, не готовый ответ.

## Необязательный PostgreSQL-маршрут

Этот маршрут требует отдельной пустой **учебной** БД, установленного PostgreSQL и
`psql`. Он не запускается default tests и не заменяет самостоятельную работу.
Пример для Linux/WSL (замените учебные credentials и имя БД; не сохраняйте их в git):

```bash
export MIGRATIONS_DATABASE_URL='postgresql+psycopg://student:student@localhost:5432/roadmap_migrations'
export MIGRATIONS_PSQL_URL='postgresql://student:student@localhost:5432/roadmap_migrations'
uv run --offline --group migrations python -m modules.02_python_backend.exercises.schema_migrations.demo --database-url "$MIGRATIONS_DATABASE_URL" --revision 0001
psql "$MIGRATIONS_PSQL_URL" -c "INSERT INTO prediction_jobs VALUES (1,'tiny-v1',1250),(2,'tiny-v2',0);"
uv run --offline --group migrations python -m modules.02_python_backend.exercises.schema_migrations.demo --database-url "$MIGRATIONS_DATABASE_URL"
psql "$MIGRATIONS_PSQL_URL" -c "SELECT * FROM prediction_jobs ORDER BY id;"
uv run --offline --group migrations python -m modules.02_python_backend.exercises.schema_migrations.demo --database-url "$MIGRATIONS_DATABASE_URL" --downgrade 0001
psql "$MIGRATIONS_PSQL_URL" -c "SELECT * FROM prediction_jobs ORDER BY id;"
```

В PowerShell переменные задаются как `$env:MIGRATIONS_DATABASE_URL = '...'` и
передаются как `$env:MIGRATIONS_DATABASE_URL`; в Windows можно использовать те же
`uv run` команды без привязки к `.venv/bin`. Различные URL нужны потому, что
`+psycopg` выбирает драйвер SQLAlchemy и не входит в URI формата psql.
Проверьте ограничения, версию и сохранение строк теми же SELECT, затем отдельно
разберите блокировки/конкурентную запись. Статус этого маршрута: **не исполнен
авторами в default проверке; требует отдельного PostgreSQL окружения**.

## Критерии защиты

Слабое: миграция прошла на пустой базе или новый ORM-класс содержит колонку.
Сильное: до/после SELECT на исходных строках, подтверждение реального backfill,
ограничение новых writes, сохранение index/ID/content при downgrade, повторный
upgrade и объяснение неуспешного перехода. Расскажите, почему `stamp head` не
заменяет upgrade и почему rollback приложения не равен downgrade схемы.

Перенос: body станет очень большим, записи продолжаются во время backfill.
Предложите порционный алгоритм с checkpoint, совместимый порядок релизов readers
и writers, условие завершения backfill и тест возобновления после середины порции.
Готовый вариант этого алгоритма не входит в starter. Для разрушительного
преобразования объясните пределы downgrade и где понадобится backup/restore.
