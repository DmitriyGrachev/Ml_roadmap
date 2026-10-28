# Collections

## Goal

Choose lists, tuples, sets, and dictionaries deliberately and use compact Python data-processing idioms.

## Java mental model

These resemble `List`, records, `Set`, and `Map`, with comprehensions often replacing small Stream pipelines. A comprehension is syntax, not a lazy Stream.

## Python model

Lists preserve order, tuples represent fixed positional values, sets test membership, and dictionaries map keys to values while preserving insertion order.

[Разбор с прогнозами, выводом примера и объяснениями](theory.md) продолжает этот вход в урок. Для вопросов об общем изменяемом объекте сначала вспомните [Object Model](../01_object_model/README.md).

## Key concepts

Use unpacking to name positional data, slicing to select ranges, and comprehensions to project or filter readable data. Sort with an explicit key when output order matters.

## Example

Run `uv run python modules/01_python_core/02_collections/example.py` to summarize document-language metadata with a set and dictionary.
Полный вывод и смысл каждого шага разобраны в [теории](theory.md#example).

## Exercises

Start with the focused collection tasks, then use the review and mini-feature to combine the ideas:

- [Detect duplicate transactions](exercises/detect_duplicates/README.md)
- [Group transaction amounts by user](exercises/group_by_user/README.md)
- [Count payment providers](exercises/provider_frequency/README.md)
- [Sort payments with multiple keys](exercises/sort_payments/README.md)
- [Filter and project event records](exercises/filter_project_events/README.md)
- [Slice transaction windows](exercises/slice_windows/README.md)
- [Unpack settlement records safely](exercises/unpack_settlements/README.md)
- [Review Java-shaped transaction grouping](code_review/java_shaped_grouping/README.md)
- [Build a transaction analytics report](../mini_features/transaction_report/README.md)

## Self-check

1. Which collection fits repeated membership checks, and what happens to duplicates?
2. How do list, tuple, set, and dict differ in order, access, and changes?
3. Why can `items[1:3]` return fewer than two items?
4. When does unpacking a row into three names fail?
5. What changes when a comprehension adds an `if` clause?
6. Why does dictionary insertion order not imply sorted order?
7. How do `sorted(..., key=...)` and `list.sort(...)` differ?

После собственной попытки сверяйтесь с [объяснениями](theory.md#answers).

## Done when

You can select a collection based on its access pattern rather than Java habit.
