# Testing exercises

## Three learner states

Exercise tests distinguish three outcomes:

1. **Expected-incomplete:** an untouched starter boundary raises `NotImplementedError` and the helper marks that one boundary as expected-incomplete.
2. **Failed attempt:** an incorrect result, import error, syntax error, assertion failure, or unexpected exception fails normally.
3. **Passed solution:** a correct implementation passes the exercise test.

This keeps the repository health check useful without pretending the learner's work is already complete.

## Run the narrowest useful command

Start from the repository root. Each exercise README will name its focused test command; later, `uv run python scripts/learn.py test python-collections` will delegate only to catalog-owned test targets. Use `uv run pytest` to check overall repository health.

## When a test fails

Read the assertion and the stated acceptance criteria before changing code. Do not modify test expectations to accept an implementation that violates the exercise contract. Preserve a passing regression test whenever you repair a genuine defect.

## Quality checks

Run `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy` before treating a learning change as complete. See the [learning rules](learning-rules.md) for the associated working habits.
