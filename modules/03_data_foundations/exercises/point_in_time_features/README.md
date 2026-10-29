# Pandas: признаки на момент запроса

ID: `data-point-in-time-features`. Сложность: средняя; 75–105 минут.

## Перед началом

Нужны [Pandas и группировки](../../02_pandas_core/README.md),
[проверки качества](../../03_data_quality/README.md) и
[временные splits и утечки](../../05_splits_and_leakage/README.md).
Разбор схемы, полуинтервала и типичных ошибок — в [theory.md](theory.md).

## Задание

Реализуйте только `build_point_in_time_features(events, queries, window)` в
[starter.py](starter.py). `events` имеет столбцы `event_id, entity_id, event_time,
amount`; `queries` — `query_id, entity_id, as_of`. ID — непустые непотерянные
значения (не NaN/None); `event_id` уникален среди событий, `query_id` среди
запросов; `entity_id` может повторяться. Входные индексы произвольны. Времена
должны уже иметь timezone-aware UTC datetime dtype, без NaT. Naive, смешанные
object-колонки и timezone кроме UTC отклоняются: вызывающий код должен явно
нормализовать их до вызова. Это предотвращает скрытое предположение о часовом поясе.
`amount` — конечное числовое значение, в том числе отрицательное; NaN/inf и строки
недопустимы даже у будущих событий. Входные DataFrame не меняются.

`window` — положительный `pd.Timedelta`, не строка и не NaT. Для каждой строки
запроса отберите только события **той же сущности** во временном полуинтервале
`[as_of-window, as_of)`. Событие слева включается; в момент запроса и позднее
исключается. События с одинаковым временем и разными ID считаются отдельно;
ответ не зависит от исходной сортировки событий.

Верните новый DataFrame с RangeIndex и колонками строго
`query_id, count, sum, mean` в **порядке строк queries**, сохраняя значения ID.
`count` имеет `int64`, `sum/mean` — `float64`. Пустая история и неизвестная
сущность: `count=0, sum=0.0, mean=NaN`. Пустые входные таблицы разрешены при
сохранённых схеме и dtype; пустой выход сохраняет объявленные типы. Ошибки
контракта отклоняйте через `ValueError`; не исправляйте невалидные данные молча.

## Проверка

Из корня репозитория:

```bash
.venv/bin/python -m modules.03_data_foundations.exercises.point_in_time_features.example
.venv/bin/python -m pytest modules/03_data_foundations/exercises/point_in_time_features -q
.venv/bin/python scripts/learn.py test data-point-in-time-features
.venv/bin/python scripts/learn.py check data-point-in-time-features
```

На Windows используйте `.venv/Scripts/python.exe`. [example.py](example.py)
разбирает одну фиксированную сущность и один запрос на других данных; он не
предоставляет общую реализацию группового временного join. Сеть, загрузки,
артефакты и optional зависимости не нужны. `test_example.py` — только авторский
разбор. Строгая граница learner completion — `test_starter.py` и функция в
`starter.py`. До реализации xfail ожидаемы; xfail/skip и авторский smoke не
засчитываются строгим `check`.

## Критерии переноса

Докажите на новых данных, что изменение будущих amount не меняет старые признаки.
Объясните, почему join только по entity размножает запросы, и почему сдвиг окна
на одну микросекунду меняет ответ на границе. Автоматические тесты проверяют
схему, утечки, временные границы и порядок; человек оценивает ваш выбор времени
доступности события в новом домене и стратегию расчёта на большом объёме.
