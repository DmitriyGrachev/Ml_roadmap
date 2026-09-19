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

Collection exercises arrive after this lesson; practice reading the result types before writing any algorithm.

## Self-check

1. Which collection is best for membership checks?
2. Does a list preserve order?
3. When is a tuple useful?
4. What does `items[1:3]` select?
5. What makes sorting deterministic?

## Done when

You can select a collection based on its access pattern rather than Java habit.
