# SQL foundations: latest valid measurements

ID `backend-sql-foundations`; средний уровень, 30–50 минут.
Prerequisite: [разбор SQL](../../07_postgresql/sql_basics.md), особенно NULL/window/ties.
Это новый узкий контракт, а не изменение прежнего analytics SQL.

Реализуйте только `latest_valid_measurements_sql() -> str` в `starter.py`.
Верните один SELECT (можно с CTE) для таблицы:

```text
measurements(id INTEGER PRIMARY KEY, device TEXT NOT NULL,
             measured_at TEXT NOT NULL, value REAL NULL)
```

`measured_at` — корректная ISO date `YYYY-MM-DD`; часовые пояса в этой задаче
не участвуют. На каждый device нужна последняя запись **с непустым value**.
При одинаковой дате выбирайте больший id. Верните ровно `device, id, value`,
одну строку на device, сортировку по device по возрастанию. Если у устройства
нет валидных значений — строки нет. Ноль и отрицательные value валидны.
Не изменяйте таблицу, не используйте внешние файлы/сеть и не возвращайте готовый
результат из Python: функция возвращает SQL, тесты выполняют его на разных данных.

Сначала нарисуйте: все события → допустимые значения → порядок внутри устройства
→ одна строка → общий порядок. Проверьте на своём примере устройство с пропуском
в самой поздней записи и с двумя валидными событиями в одну дату.

```powershell
uv run python scripts/learn.py test backend-sql-foundations
uv run python scripts/learn.py check backend-sql-foundations
```

Автотесты проверяют строки на SQLite, включая пустую таблицу, NULL, ties,
отрицательные/нулевые значения и сортировку. Незавершённый TODO — xfail для test,
отказ в строгом check. **PostgreSQL не считается проверенным** этими тестами.
Когда будет явно доступен PostgreSQL, перенесите ту же схему/данные в отдельную
учебную schema и сравните строки и типы; используйте прежний opt-in маршрут.
Понимание проверяется объяснением порядка фильтрации и выбора последней записи,
а не способностью воспроизвести один ответ из demo.
