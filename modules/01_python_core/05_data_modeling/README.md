# Data modeling

## Goal

Model domain values with dataclasses, composition, properties, and focused behavior.

[Теория: объект-значение, конструктор и границы frozen](theory.md) — разбор
`PageSpan` с прогнозами, отдельными пробами Decimal/ASCII и командами запуска.
После чтения объясните инвариант на новом значении, затем переходите к
существующему `python-payment-model`. Авторская демонстрация не заполняет стартер
и не меняет progress.

## Java mental model

A frozen dataclass resembles a record. It is not a complete substitute for Java's inheritance and constructor-validation conventions.

## Python model

Use `@dataclass` for data-focused objects, composition for collaborating behavior, ABCs for necessary runtime abstraction, and protocols when shape is enough.

## Key concepts

`frozen=True` expresses immutable fields after construction. Properties can protect a useful derived invariant, but a plain attribute is clearer when no behavior is needed.

## Example

Run `uv run python modules/01_python_core/05_data_modeling/example.py` to create a frozen ledger entry with a decimal amount.

## Exercises

- [Model an immutable payment](exercises/payment_model/README.md)

## Self-check

1. When does a dataclass help?
2. What does `frozen=True` express?
3. Why prefer composition often?
4. When might a property help?
5. How does a protocol differ from an ABC?

## Done when

You can choose a small value object rather than a Java-style mutable POJO by default.
