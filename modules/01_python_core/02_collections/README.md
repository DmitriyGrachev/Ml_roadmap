# Collections

## Goal

Choose lists, tuples, sets, and dictionaries deliberately and use compact Python data-processing idioms.

## Java mental model

These resemble `List`, records, `Set`, and `Map`, with comprehensions often replacing small Stream pipelines. A comprehension is syntax, not a lazy Stream.

## Python model

Lists preserve order, tuples represent fixed positional values, sets test membership, and dictionaries map keys to values while preserving insertion order.

## Key concepts

Use unpacking to name positional data, slicing to select ranges, and comprehensions to project or filter readable data. Sort with an explicit key when output order matters.

## Example

Run `uv run python modules/01_python_core/02_collections/example.py` to summarize document-language metadata with a set and dictionary.

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

1. Which collection is best for membership checks?
2. Does a list preserve order?
3. When is a tuple useful?
4. What does `items[1:3]` select?
5. What makes sorting deterministic?

## Done when

You can select a collection based on its access pattern rather than Java habit.
