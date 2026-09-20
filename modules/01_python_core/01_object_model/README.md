# Object model

## Goal

Reason accurately about names, references, mutation, equality, truthiness, and `None`.

## Java mental model

Java combines object references with declared static typing checked largely before runtime. Python's `is` is identity, while `==` is value comparison; it is not Java's `==` for object references.

## Python model

Python is dynamically typed: names bind to objects rather than keeping one declared type, and invalid operations fail at runtime. Mutating a list is observable through every name bound to that list, while rebinding changes only one name. Type hints help tools and readers without turning Python into Java's runtime model.

## Key concepts

Use `is` for singleton checks such as `value is None`; use `==` for values. Empty containers are falsey, but distinguish an empty value from a missing value when the domain requires it. Python conventions such as `snake_case`, direct iteration, and clear truth tests support Pythonic style: readable code that follows the language's usual data model instead of imitating Java syntax.

## Example

Run `uv run python modules/01_python_core/01_object_model/example.py` to compare two equal but distinct support-ticket tag lists.

## Exercises

Predict which example operations mutate or rebind, then [continue to collection practice](../02_collections/README.md#exercises).

## Self-check

1. What does `is` compare?
2. What does `==` compare?
3. Why prefer `is None`?
4. Is an empty list truthy?
5. What is the difference between mutation and rebinding?
6. How does dynamic typing differ from Java static typing?
7. What makes a style choice Pythonic rather than merely valid Python?

## Done when

You can explain why two equal lists need not be the same object.
