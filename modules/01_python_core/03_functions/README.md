# Functions

## Goal

Use functions as values and write clear callable boundaries with explicit arguments.

## Java mental model

Functions are close to functional interfaces and lambdas. Python functions are first-class objects without declaring a dedicated interface for each use.

## Python model

Pass functions, return them, capture configuration in closures, and choose positional-only, positional-or-keyword, keyword-only, and defaulted arguments deliberately.

[Разбор вызова, замыканий и итерации с прогнозами](theory.md) продолжает этот вход в урок. Общие объекты и перепривязку имён напоминает [Object Model](../01_object_model/README.md).

## Key concepts

`/` marks positional-only parameters and `*` marks keyword-only parameters. `*args` collects extra positional arguments into a tuple, while `**kwargs` collects extra keyword arguments into a dict. At a call site, the same markers unpack an iterable or mapping to forward arguments. Defaults are evaluated once, so avoid mutable defaults. `enumerate` supplies indexes and `zip` pairs aligned iterables. Prefer a named function when a lambda would hide business intent.

## Example

Run `uv run python modules/01_python_core/03_functions/example.py` to send a notification through a formatting callback.
Полный вывод и путь аргумента через callback разобраны в [теории](theory.md#example).

## Exercises

- [Build a configurable transaction filter](exercises/configurable_filter/README.md)
- [Combine provider responses](exercises/combine_responses/README.md)
- [Debug leaking audit tags](debugging/mutable_defaults/README.md)
- [Review a stateful report builder](code_review/stateful_report/README.md)

## Self-check

1. Can a function be stored in a variable?
2. What does `*` in a signature mean?
3. Why avoid mutable default values?
4. What is a closure?
5. When is a named function clearer than a lambda?
6. What do `enumerate` and `zip` provide?
7. What do `*args` and `**kwargs` collect, and how do the same markers forward values?

Сначала ответьте на новом примере, затем откройте [объяснения](theory.md#answers).

## Done when

You can pass behavior without introducing a stateful helper class.
