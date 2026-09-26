# Testing exercises

## Three learner states

Exercise tests distinguish three outcomes:

1. **Expected-incomplete:** an untouched starter boundary raises `NotImplementedError` and the helper marks that one boundary as expected-incomplete.
2. **Failed attempt:** an incorrect result, import error, syntax error, assertion failure, or unexpected exception fails normally.
3. **Passed solution:** a correct implementation passes the exercise test.

This keeps the repository health check useful without pretending the learner's work is already complete.

## Run the narrowest useful command

Start from the repository root. Each exercise README names its focused test command;
`uv run python scripts/learn.py test python-collections` delegates only to catalog-owned test
targets. Use `uv run pytest` to check overall repository health.

The full suite also contains maintainer checks that require the distributed starter template to
remain unsolved (`tests/integration/test_repository_hygiene.py`). Once you implement a starter,
those particular assertions can fail by design. Judge your answer using the focused task command,
not by restoring `NotImplementedError` to satisfy template hygiene.

For neutral practice in every module, see the [Medium exercise map](neutral-practice.md).
Modules 04–08 examples run locally; provider doubles test LLM application contracts, not the
quality or safety of a real model. Retrieval fixtures and operational simulations likewise do not
establish live retrieval quality or production readiness. An untouched starter remains `XFAIL`,
not a passed solution.

## When a test fails

Read the assertion and the stated acceptance criteria before changing code. Do not modify test expectations to accept an implementation that violates the exercise contract. Preserve a passing regression test whenever you repair a genuine defect.

## Quality checks

Run `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy` before treating a learning change as complete. See the [learning rules](learning-rules.md) for the associated working habits.
