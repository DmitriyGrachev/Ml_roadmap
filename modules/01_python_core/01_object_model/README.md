# Object model

## Goal

Reason accurately about names, references, mutation, equality, truthiness, and `None`.

## Java mental model

References and `equals` are familiar. Python's `is` is identity, while `==` is value comparison; it is not Java's `==` for object references.

## Python model

Names bind to objects. Mutating a list is observable through every name bound to that list, while rebinding changes only one name.

## Key concepts

Use `is` for singleton checks such as `value is None`; use `==` for values. Empty containers are falsey, but distinguish an empty value from a missing value when the domain requires it.

## Example

Run `uv run python modules/01_python_core/01_object_model/example.py` to compare two equal but distinct support-ticket tag lists.

## Exercises

Later exercises use mappings and collections; first predict whether an operation mutates or returns a new value.

## Self-check

1. What does `is` compare?
2. What does `==` compare?
3. Why prefer `is None`?
4. Is an empty list truthy?
5. What is the difference between mutation and rebinding?

## Done when

You can explain why two equal lists need not be the same object.
