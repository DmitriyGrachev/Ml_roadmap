# SQL с нуля: от строки к группе и окну

Зачем: выбрать нужные измерения датчиков в базе, не загружая всю таблицу в Python.
Сначала пройдите [Python-вход](../../01_python_core/00_environment/basics.md).
Опыт [работы с таблицами](../../03_data_foundations/02_pandas_core/README.md)
поможет связать идеи, но Pandas не требуется: маленькие таблицы объясняются здесь.
Затем вернитесь к [SQLAlchemy](../06_sqlalchemy/README.md): ORM использует SQL,
но не объясняет автоматически смысл соединения и число полученных строк.
Это сопровождение существующего PostgreSQL-урока, не отдельный курс баз данных.

## 1. Таблица, строка и SELECT

Представьте журнал показаний: **таблица (table)** состоит из строк (rows) и
именованных столбцов (columns). Один `readings.id` определяет одно измерение;
`station_id` указывает станцию. Идентификатор — ключ (key), не номер строки на экране.

Исходные маленькие таблицы [исполняемой демонстрации](sql_basics_demo.py):

| stations.id | name |
| --- | --- |
| 1 | north |
| 2 | south |
| 3 | west |

| readings.id | station_id | value, условные единицы |
| --- | --- | --- |
| 1 | 1 | 8 |
| 2 | 1 | NULL |
| 3 | 2 | 12 |
| 4 | 2 | 12 |

`SELECT id, value FROM readings` выбирает столбцы; `FROM` задаёт таблицу.
SQL — декларативный язык (declarative): вы описываете требуемые строки,
а план выполнения выбирает СУБД. Порядок без `ORDER BY` **не гарантирован**.
SQL `=` — сравнение; это не Python-присваивание.

```sql
SELECT id, value
FROM readings
WHERE value >= 10
ORDER BY value DESC, id ASC;
```

Прогноз: сколько строк останется? Результат `(3, 12), (4, 12)`.
`WHERE` оставляет строки с истинным условием, `DESC` сортирует по убыванию,
`ASC` по возрастанию. Второй ключ `id` разрешает равенство (tie).
`;` завершает SQL-инструкцию; ключевые слова здесь написаны прописными для чтения.

```text
readings: 4 строки
    → WHERE value >= 10: 2 строки
    → SELECT id,value: 2 столбца
    → ORDER BY value DESC,id: стабильный для этих уникальных id порядок
```

Это логическая схема понимания, не обещание физического query plan.
Как БД выбирает scan/index, уже разобрано в [analytics SQL](../exercises/analytics_sql/plan_theory.md).

## 2. NULL — неизвестно, а не ноль

`NULL` обозначает отсутствие значения. `value = NULL` не становится True даже
у строки с пропуском; сравнение даёт UNKNOWN. `WHERE` пропускает только True,
поэтому результат пуст. Используйте `IS NULL` / `IS NOT NULL`:

| операция | результат по readings.id |
| --- | --- |
| `WHERE value = NULL` | пусто |
| `WHERE value IS NULL` | 2 |
| `WHERE value IS NOT NULL` | 1, 3, 4 после ORDER BY id |

`value=0` было бы реальным нулевым измерением. Подстановка `COALESCE(value, 0)`
возвращает первый не-NULL аргумент, но её смысл нужно обосновать: неизвестное
значение нельзя автоматически объявить нулём. Здесь пропуск сохраняется.

Типичная ошибка: сортировать по двум полям, но не определить положение NULL.
Для переносимости нашего окна явно задано `NULLS LAST`. Значения по умолчанию
и типы отличаются между SQLite/PostgreSQL; одинаковая картинка не равна проверке диалекта.

## 3. GROUP BY и HAVING: одна строка на группу

Нужно суммировать **измерения станции**, а не весь журнал. `GROUP BY station_id`
разбивает строки на группы, агрегат (aggregate) сворачивает каждую группу в число.
`COUNT(*)` считает строки, `COUNT(value)` — только непустые значения,
`SUM`/`AVG` пропускают NULL; сумма без непустых значений — NULL, а не 0.

Чтобы не потерять west без измерений, соединяем stations с readings через LEFT JOIN:

```sql
SELECT s.name, COUNT(r.id), COUNT(r.value), SUM(r.value)
FROM stations s LEFT JOIN readings r ON r.station_id = s.id
GROUP BY s.id, s.name
ORDER BY s.name;
```

`s` и `r` — короткие псевдонимы таблиц (aliases); `r.id` уточняет, чей столбец.
После LEFT JOIN у west есть одна служебная результирующая строка с NULL полями r.
Поэтому `COUNT(*)` ошибочно дал бы для west 1; `COUNT(r.id)` даёт 0.

| станция | исходных readings | непустых value | сумма |
| --- | --- | --- | --- |
| north | 2 | 1 | 8 |
| south | 2 | 2 | 24 |
| west | 0 | 0 | NULL |

`WHERE` фильтрует отдельные строки **до** группировки. `HAVING AVG(r.value) >= 10`
фильтрует группы после вычисления среднего: в примере `having` остаётся только
`south, 12.0`. Если сперва написать `WHERE value >= 10`, вы посчитаете среднее
уже по усечённым измерениям: это другой вопрос. Вариация: что изменится, если
для north добавить третье измерение 20? Сначала пересчитайте count/sum/avg вручную.

## 4. JOIN: совпадение ключей может размножить строки

`JOIN ... ON ...` создаёт **все** пары строк, удовлетворяющие условию.
Это не Pandas-присваивание по индексу и не гарантия «одна строка на объект».
`INNER JOIN` оставляет совпавшие пары, `LEFT JOIN` также сохраняет каждую левую
строку без совпадений, добавляя справа NULL. Связь many-to-many может увеличить
число строк; сам JOIN не удаляет дубликаты и не выбирает «первый» вариант.

Таблица tags: `(1, indoor), (1, quiet), (2, outdoor)`.

```sql
SELECT r.id, t.tag
FROM readings r JOIN tags t ON t.station_id = r.station_id
ORDER BY r.id, t.tag;
```

| группа соединения | слева readings | справа tags | пар |
| --- | --- | --- | --- |
| station_id=1 | id 1,2: две строки | indoor,quiet: две строки | 2×2=4 |
| station_id=2 | id 3,4: две строки | outdoor: одна | 2×1=2 |

Результат: `(1,indoor),(1,quiet),(2,indoor),(2,quiet),(3,outdoor),(4,outdoor)`.
Четыре readings превратились в **шесть** строк. Если теперь суммировать value,
показание north=8 будет учтено два раза. Исправление выбирают по вопросу: агрегировать
до JOIN, обеспечить уникальный правый ключ, использовать EXISTS для проверки наличия.
`DISTINCT` после неверного JOIN не является универсальным исправлением: он может
скрыть и настоящие повторные события.

Самостоятельно предскажите результат LEFT JOIN stations→readings: почему три станции
дадут пять строк, а не три? Какие поля у строки west? Когда фильтр `WHERE r.value > 0`
уберёт эту строку, несмотря на LEFT JOIN?

## 5. Оконная функция сохраняет отдельные строки

Задача: упорядочить измерения **внутри** станции и увидеть равные значения.
`GROUP BY` свернул бы строки; оконная функция (window function) добавляет вычисленное
значение к каждой строке. `OVER` задаёт окно, `PARTITION BY` — независимые разделы.

```sql
ROW_NUMBER() OVER (
  PARTITION BY s.id ORDER BY r.value DESC NULLS LAST, r.id
)
DENSE_RANK() OVER (
  PARTITION BY s.id ORDER BY r.value DESC NULLS LAST
)
```

Полный SELECT находится в `QUERIES["windowed"]` демонстрации. `ROW_NUMBER` назначает
уникальные позиции, а `DENSE_RANK` присваивает одинаковым значениям одинаковый ранг
без пропуска следующего ранга. Условия сортировки различаются намеренно: `id`
разрешает tie для позиции, но не должен разрушать равенство значений для ранга.

| id | station | value | row_number | dense_rank |
| --- | --- | --- | --- | --- |
| 1 | north | 8 | 1 | 1 |
| 2 | north | NULL | 2 | 2 |
| 3 | south | 12 | 1 | 1 |
| 4 | south | 12 | 2 | 1 |

Всё ещё четыре строки. Вычисленный window alias нельзя фильтровать в WHERE того
же уровня SELECT: используйте подзапрос или CTE (`WITH name AS (...)`) и внешний
SELECT. Внутренний запрос формирует таблицу, внешний выбирает нужные её строки.
Для «последнего измерения» нужна сортировка по времени, а не по величине value;
это отдельная [самостоятельная задача](../exercises/sql_foundations/README.md).

## 6. Запуск, практика и границы проверки

Из корня, без PostgreSQL/Docker и без внешней сети:

```powershell
uv run python -m modules.02_python_backend.07_postgresql.sql_basics_demo
uv run pytest modules/02_python_backend/tests/test_sql_basics_demo.py -q
uv run python scripts/learn.py test backend-sql-foundations
uv run python scripts/learn.py check backend-sql-foundations
```

Демонстрация печатает engine/version и все семь результатов из таблиц выше.
Unit tests исполняют запросы в свежей **SQLite in-memory**: это проверка строк,
NULL, ties и кратности JOIN, **не PostgreSQL integration PASS**. В этой среде
проверено SQLite 3.53.1 / Python 3.12; PostgreSQL runtime отдельно NOT_RUN.
Следом — прежние [postgres_query](exercises/postgres_query/README.md),
[analytics SQL](../exercises/analytics_sql/README.md) и только после готового API —
[практикум контейнера](../09_docker_delivery/container_practice.md).

Для защиты объясните: какую единицу представляет строка до/после JOIN;
почему COUNT(*) и COUNT(r.id) расходятся; WHERE/HAVING; порядок и ties;
почему latest valid требует отфильтровать NULL **до** выбора последнего события.
Синтаксически работающий SQL не гарантирует правильный вопрос или зерно агрегации.

Официальные источники, английский, проверено 28.10.2026:
[PostgreSQL tutorial §2.5–2.7](https://www.postgresql.org/docs/current/tutorial-sql.html),
[§2.6 JOIN](https://www.postgresql.org/docs/current/tutorial-join.html),
[§3.5 Window Functions](https://www.postgresql.org/docs/current/tutorial-window.html),
[Comparison predicates / NULL](https://www.postgresql.org/docs/current/functions-comparison.html).
Читайте только названные разделы: индексы и эксплуатация уже относятся к другим
имеющимся урокам. Проверка официального описания не заменяет запуск на PostgreSQL.
