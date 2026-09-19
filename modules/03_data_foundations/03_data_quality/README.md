# Data quality checks

## Goal

Measure missing, duplicate, invalid, and unexpected data before an analysis or model relies on it.

## Java mental model

Validation is not only a DTO-construction concern: a DataFrame can contain a mixture of valid, missing, and duplicated values that needs aggregate evidence.

## Python model

Use null-aware operations and duplicate masks to produce an explicit quality report; decide whether a transformation may mutate its caller before writing it.

## Key concepts

Missing values, duplicates, parsing, schema expectations, quality counts, mutation policy, and data contracts.

## Example

`example.py` counts repeated document identifiers and missing language metadata in a small document intake batch.

## Exercises

The quality-report exercise has a wider transaction schema and additional invalid-value checks, so this document example does not expose its answer.

## Self-check

1. Is an empty string necessarily a missing value?
2. What does `duplicated` count by default?
3. Why should quality counts be reproducible?
4. When is it safer to return a copy?
5. What quality check would you run before parsing timestamps?

## Done when

You can distinguish duplicate records from missing fields and explain the chosen counting policy.
