# Exceptions and I/O

## Goal

Handle failures narrowly and use context managers for files, paths, JSON, and CSV safely.

## Java mental model

`try`/`except` and `with` resemble exceptions plus try-with-resources. Python does not distinguish checked exceptions in the Java sense.

## Python model

Catch only errors you can handle, let unexpected problems remain visible, and use `pathlib.Path` plus `with` to scope resource lifetimes.

## Key concepts

Context managers guarantee cleanup around a block. For CSV, open files with `newline=""`, use `csv.DictReader` or `DictWriter`, and validate required headers before processing rows. For replacement, write a temporary file near the destination and replace only after successful serialization.

## Example

Run `uv run python modules/01_python_core/06_exceptions_io/example.py` to export a small JSON document inside a temporary directory.

## Exercises

Later practice asks for an atomic JSON export with explicit error behavior.

## Self-check

1. Why catch narrow exception types?
2. What closes a file opened in `with`?
3. Why use `Path`?
4. What makes an export atomic?
5. When should an exception propagate?
6. Why does CSV file opening use `newline=""`?

## Done when

You can explain how a context manager protects a resource even during failure.
