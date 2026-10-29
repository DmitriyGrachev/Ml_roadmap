# Module 01 — Python core for Java developers

This module moves from a reliable local workflow through Python's data model,
collections, functions, types, I/O, generators, decorators, testing, and async
I/O. Read lessons in numeric order, run each `example.py`, and use the practice
map to move from focused drills to the mini-feature.

| Lesson | Focus |
| --- | --- |
| [00](00_environment/README.md) | Environment and workflow |
| [01](01_object_model/README.md) | References, mutability, and equality |
| [02](02_collections/README.md) | Collections and idiomatic data processing |
| [03](03_functions/README.md) | Functions and callbacks |
| [04](04_typing/README.md) | Types and protocols |
| [05](05_data_modeling/README.md) | Classes and dataclasses |
| [06](06_exceptions_io/README.md) | Exceptions and I/O |
| [07](07_iterators_generators/README.md) | Iterators and generators |
| [08](08_decorators/README.md) | Decorators |
| [09](09_testing/README.md) | pytest fundamentals |
| [10](10_asyncio/README.md) | asyncio I/O concurrency |

## Practice map

### Standalone Medium exercise

- [Merge calendar intervals](exercises/calendar_intervals/README.md) — combine
  overlapping appointments with validation and immutable interval records.

### First sprint — 10 coding exercises

- [Detect duplicate transactions](02_collections/exercises/detect_duplicates/README.md)
- [Group transaction amounts by user](02_collections/exercises/group_by_user/README.md)
- [Count payment providers](02_collections/exercises/provider_frequency/README.md)
- [Sort payments with multiple keys](02_collections/exercises/sort_payments/README.md)
- [Filter and project event records](02_collections/exercises/filter_project_events/README.md)
- [Slice transaction windows](02_collections/exercises/slice_windows/README.md)
- [Unpack settlement records safely](02_collections/exercises/unpack_settlements/README.md)
- [Build a configurable transaction filter](03_functions/exercises/configurable_filter/README.md)
- [Combine provider responses](03_functions/exercises/combine_responses/README.md)
- [Delegate through a payment-processor protocol](04_typing/exercises/payment_processor_protocol/README.md)

### Debugging — 2 tasks

- [Debug leaking audit tags](03_functions/debugging/mutable_defaults/README.md)
- [Debug an exhausted amount iterator](07_iterators_generators/debugging/iterator_exhaustion/README.md)

### Code review — 2 tasks

- [Review Java-shaped transaction grouping](02_collections/code_review/java_shaped_grouping/README.md)
- [Review a stateful report builder](03_functions/code_review/stateful_report/README.md)

### Mini-feature

- [Build a transaction analytics report](mini_features/transaction_report/README.md)

### Later lessons — 6 coding exercises

- [Model an immutable payment](05_data_modeling/exercises/payment_model/README.md)
- [Export JSON atomically](06_exceptions_io/exercises/json_export/README.md)
- [Stream NDJSON transactions lazily](07_iterators_generators/exercises/stream_transactions/README.md)
- [Retry selected gateway failures](08_decorators/exercises/retry_gateway/README.md)
- [Test one provider interaction](09_testing/exercises/mock_provider/README.md)
- [Fetch quotes concurrently](10_asyncio/exercises/fetch_quotes/README.md)

Run all runnable examples with `uv run pytest modules/01_python_core/tests -q`.

### Additional neutral-domain practice

- [Build a word index](exercises/word_index/README.md) — Beginner: sets, dictionaries, and text.
- [Batch a one-shot stream](exercises/paged_stream/README.md) — Medium: lazy generic iterators.
- [Bound concurrent station fetches](exercises/bounded_fetch/README.md) — Medium: asyncio limits and cleanup.
- [Компактные Python-вариации для интервью](exercises/interview_patterns/README.md) — поиск, top-k и обход графа.

### Обязательное продолжение для ML Engineer

После основ asyncio прочитайте [жизненный цикл задач](exercises/async_lifecycle/README.md):
semaphore, ошибка дочерней задачи, timeout, внешняя отмена и cleanup.
Это также prerequisite к прежнему `python-bounded-fetch`.
После modules/imports и tests выполните [доставку Python-пакета](exercises/package_delivery/README.md):
wheel в чистом окружении и общий preprocessing для обучения и API.
Порядок и строгие зачёты — в [текущей карте](../../docs/learning-map.md).
