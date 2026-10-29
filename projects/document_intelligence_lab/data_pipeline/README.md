# ML data pipeline: SQL, increment, idempotency, replay

ID: `ml-data-pipeline` · самостоятельное упражнение.
Пререквизиты: Python SQL/transaction, preprocessing и Document Intelligence bundle,
train/validation/test split. Следующий шаг: [production lifecycle](../production_readiness/README.md)
и [один AWS bridge](../production_readiness/deployment.md).

## Теория и контракт

Pipeline превращает append-only события в актуальную таблицу документов. Это ещё
не training pipeline: split по времени/источнику надо заморозить отдельно до fit.
Случайное обновление train данными из будущего делает replay технически верным,
но оценку модели недостоверной. Доступность признака определяется моментом prediction,
а не тем, что поле оказалось в сегодняшнем SQL dump.

`raw_events`: `ingest_id INTEGER PRIMARY KEY`, `event_id`, `doc_id`, `event_time`,
`text`, `label`. ingest_id — последовательность поступления, event_time — время
события. Поздний документ с event_time=5 после события time=20 должен попасть в
обработку. Поэтому SQL извлекает `WHERE ingest_id > :cursor ORDER BY ingest_id
LIMIT :limit`, а не `WHERE event_time > MAX(event_time)`. Параметры передаются
драйверу, а не конкатенируются в SQL. В примере время — целые условные UTC ticks;
в реальном контракте нужны единицы, timezone, precision и политика clock skew.

`documents(doc_id PK,event_time,ingest_id,text,label)` хранит последнюю версию по
(event_time, ingest_id). Новый для нас late doc принимается, устаревшая версия
уже известного doc не перетирает новую. При равных event_time побеждает больший
ingest_id; это явная политика tie-break, её надо согласовать с источником.
`processed(event_id PK,payload_sha256)` различает точный duplicate и конфликт:
повтор event_id с теми же bytes-полями пропускается; с другим payload идёт в
`quarantine(ingest_id PK,reason)`. Digest считается до normalization — разный raw
payload нельзя незаметно объявить тем же событием. Idempotency здесь относится
к обработке повторов, а не к бизнес-эквивалентности всех текстов.

Quality gate до upsert: непустые event_id/doc_id, неотрицательное целое event_time,
text 1..10000 непустых символов, label из circle/square/triangle. Invalid record
сохраняет reason и ingest_id, не ломает весь поток. Неудавшийся системный write,
напротив, откатывает весь batch. Нельзя ловить любую ошибку и двигать watermark:
так исчезнут необработанные строки. Source cursor, dedup, rejects и documents
коммитятся одной транзакцией. Тест с SQL trigger имитирует сбой после первого
write и требует откатить и строку, и cursor.

SQLite `BEGIN IMMEDIATE` сериализует одного writer. Этот пример предполагает
immutable append-only источник и одного pipeline worker. Изменения/удаления старых
source rows, gaps после restore и конкурентные writers требуют CDC/transactional
outbox, source offsets и протокола claim/lock. Не переносите этот код в PostgreSQL
механической заменой connection string: понадобится миграция DDL, `ON CONFLICT`,
row locking/ownership и отдельный реальный тест. PostgreSQL здесь **NOT_RUN**.
Распределённое «exactly once» не доказано; проверен локальный атомарный commit и
идемпотентный replay на явном ограниченном контракте.

Manifest фиксирует schema/transform version, точный extract SQL, watermark,
source_sha256 всех raw rows до cursor, canonical sorted output rows + rows_sha256,
quarantine + count. UTF-8 JSON: sorted keys, no NaN, newline; timestamps запуска
не входят в content identity. Одинаковые source + transform + watermark должны
дать одинаковый manifest при batch=2 и batch=100. Batch counts отдельно: число
upserted может зависеть от промежуточных версий, поэтому не является final row count.

Parquet — колонночный disk format: schema, compression, column pruning, row groups;
подходит для аналитических snapshot, но не заменяет маленькие transactional upsert.
Arrow — типизированное columnar представление данных в памяти и интерфейс обмена,
а не scheduler и не гарантия отсутствия копий для любой операции. При optional
экспорте в Parquet сохраните schema/timezone/null semantics и hash bytes самого
файла; отдельно semantic rows hash, потому что разные writer versions/compression
могут давать разные bytes одному содержимому. PyArrow не обязательная зависимость:
здесь JSON делает весь контракт обозримым. Сначала воспроизведите content identity,
потом добавляйте Arrow/Parquet, partitioning и orchestration по масштабу задачи.

## Авторский разбор

```bash
python -m projects.document_intelligence_lab.data_pipeline.demo --output /tmp/pipeline-author-run
python -m pytest projects/document_intelligence_lab/data_pipeline/test_demo.py -q
```

Первые два события создают a/time10, затем a/time20. Третье — duplicate e2.
Четвёртое — новый поздний b/time5: принимается. Пятое — a/time1: dedup запоминает,
но актуальную a не меняет. Последние два не проходят quality gate. Batch=2
проходит четыре итерации, повтор без новых событий не меняет manifest, fresh replay
batch=100 даёт тот же content. В output только events.json, manifest.json, run.json;
временные базы in-memory. Авторский `AUTHOR_SQLITE_DEMO` не learner evidence.

## Независимое задание

Реализуйте `initialize`, `load_increment`, `snapshot` в `starter.py`. Не импортируйте
реализацию `demo`. Схема и canonical manifest соответствуют описанному контракту;
точные поля видны в `demo.snapshot`, а поведение проверяется `test_starter.py`.
Возврат `load_increment`: extracted, duplicates, quarantined, upserted, watermark.
Проверяйте integer limit 1..10000. Не меняйте текущие learner completion ticks.

Создайте свой fixture минимум из 8 событий: >=2 docs, точный duplicate, конфликт
payload, late unseen doc, stale update, invalid text и нормальный update. Проведите
несколько batch=2, empty rerun и fresh replay. Добавьте fault между записью строк
и cursor и объясните rollback. Экспортируйте NEW output (не коммитить результаты):

- `events.json`: ваши raw objects event_id/doc_id/event_time/text/label;
- `manifest.json`: snapshot с полями описанного контракта;
- `run.json`: schema_version=1, exercise_id=ml-data-pipeline,
  evidence_kind=STUDENT_SQL_PIPELINE, code_sha256 текущего starter.py;
- `batches`: каждый непустой batch=2 с точными counts; `analysis` с непустыми
  watermark_late_data, dedup_conflict, transaction_failure, replay, parquet_arrow,
  cloud_mapping; `postgres` и `cloud` = NOT_RUN, пока их не запускали.

```bash
export ROADMAP_PIPELINE_EVIDENCE=/absolute/path/to/your/pipeline-run
python -m pytest projects/document_intelligence_lab/data_pipeline/test_starter.py -q
python -m pytest -p roadmap_tools.strict_check \
  projects/document_intelligence_lab/data_pipeline/test_starter.py -q
```

Windows PowerShell: `$env:ROADMAP_PIPELINE_EVIDENCE='C:\absolute\pipeline-run'`.
Отсутствующий результат даёт default xfail / strict fail. Gate вызывает именно ученические initialize/load_increment/snapshot на saved source,
сверяет их manifest/counts и saved artifact с trusted expected result. Затем
повторяет learner replay в другой чистой базе с batch=100 и empty rerun.
Пустой/константный неправильный snapshot не получает completion. Отдельно требуются
exact duplicate, conflicting payload повторного event_id, invalid text, late unseen
document и stale update; один stale timestamp не заменяет late unseen doc. Он не может доказать авторство текста/исходного запуска:
нужна защита, демонстрация своего кода и новый input от reviewer.

## Рубрика и перенос

Слабое доказательство: один SELECT, watermark по MAX(event_time), «upsert убирает
все duplicates», report только с итоговым числом строк. Сильное: raw source,
точная политика identity/conflict/tie-break, воспроизводимый hash, atomic rollback,
счётчики всех категорий, анализ quarantined и late rows, ограничения single writer.
На защите без подсказок добавьте событие с новым doc_id и старым event_time;
объясните отличия source/output hash и почему pipeline не гарантирует честный split.
Transfer: источник теперь может исправлять уже присланные события, label приходит
через неделю, две jobs запускаются одновременно. Сформулируйте новый контракт до
выбора Airflow/Spark. Эти инструменты — role-specific extension, не замена SQL
корректности и не обязательное условие этого упражнения.
