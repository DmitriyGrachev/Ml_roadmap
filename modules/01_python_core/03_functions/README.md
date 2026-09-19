# Functions

## Goal

Use functions as values and write clear callable boundaries with explicit arguments.

## Java mental model

Functions are close to functional interfaces and lambdas. Python functions are first-class objects without declaring a dedicated interface for each use.

## Python model

Pass functions, return them, capture configuration in closures, and choose positional-only, positional-or-keyword, keyword-only, and defaulted arguments deliberately.

## Key concepts

`/` marks positional-only parameters and `*` marks keyword-only parameters; defaults are evaluated once, so avoid mutable defaults. `enumerate` supplies indexes and `zip` pairs aligned iterables. Prefer a named function when a lambda would hide business intent.

## Example

Run `uv run python modules/01_python_core/03_functions/example.py` to send a notification through a formatting callback.

## Exercises

Later tasks build configurable predicates and combine independent provider responses.

## Self-check

1. Can a function be stored in a variable?
2. What does `*` in a signature mean?
3. Why avoid mutable default values?
4. What is a closure?
5. When is a named function clearer than a lambda?
6. What do `enumerate` and `zip` provide?

## Done when

You can pass behavior without introducing a stateful helper class.
