# Iterators and generators

## Goal

Process values lazily and recognize when an iterable can be consumed only once.

## Java mental model

An iterator and a generator resemble `Iterable` and Stream traversal. A Python generator is not reusable like a collection or necessarily like a freshly created stream pipeline.

## Python model

An iterable can create an iterator; an iterator yields successive values; a generator function creates an iterator lazily using `yield`.

## Key concepts

Generator expressions and generator functions defer work until iteration. Materialize once only when multiple passes, indexing, or durable storage are genuinely required.

## Example

Run `uv run python modules/01_python_core/07_iterators_generators/example.py` to stream two document-processing log lines.

## Exercises

- [Debug an exhausted amount iterator](debugging/iterator_exhaustion/README.md)
- [Stream NDJSON transactions lazily](exercises/stream_transactions/README.md)

## Self-check

1. What does `iter(value)` produce?
2. Is a generator reusable after consumption?
3. When is laziness useful?
4. What does `yield` create?
5. When should you materialize an iterable?

## Done when

You can identify APIs that must support a one-shot generator input.
