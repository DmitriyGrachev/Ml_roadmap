# Learning rules

## Work the starter, not the test

Exercises define a boundary in starter code. Change the stated editable file; keep the supplied test expectations as feedback about the behavior you need to produce.

## Use small, verifiable steps

Read the lesson, run its scoped command, make one small change, and run the same command again. When a later lesson names a more focused command, prefer it over a repository-wide run while iterating.

## Preserve the intended incomplete state

An untouched starter boundary raises `NotImplementedError`. Its exercise test appears as expected-incomplete. A wrong attempted implementation must fail normally; do not catch broad exceptions just to make a test suite look green.

## Build Python mental models, not Java replicas

Use Java and Spring comparisons to orient yourself, then learn where the comparison stops. Prefer Python data structures, functions, protocols, modules, and explicit composition when they fit the problem.

## Keep progress manual and honest

Update [progress.md](../progress.md) yourself with `[ ]`, `[~]`, or `[x]`. The command-line status view reads the file but never rewrites it.

## Protect the learning data

Use deterministic synthetic data only. Treat decimal amounts, timezone-aware timestamps, input validation, and test isolation as normal engineering requirements rather than optional polish.
