# Testing

## Goal

Write direct pytest checks with fixtures, parametrization, exception assertions, and focused mocks.

## Java mental model

pytest covers a role similar to JUnit. Its fixture injection and plain `assert` style are conventions, not Java annotations and assertion APIs.

## Python model

Tests are functions discovered by name. Parametrization keeps one behavior readable across representative inputs; fixtures make setup explicit.

## Key concepts

Assert real outcomes and use mocks at external or slow boundaries. `pytest.raises` documents expected error behavior without swallowing unrelated failures.

## Example

Run `uv run python modules/01_python_core/09_testing/example.py` to see a currency rule whose cases fit naturally in a parametrized test.

## Exercises

- [Test one provider interaction](exercises/mock_provider/README.md)

## Self-check

1. How does pytest discover a test?
2. When helps parametrization?
3. What is a fixture for?
4. When should a mock be used?
5. What does `pytest.raises` assert?

## Done when

You can choose a small behavior and express its expected outcome directly.
