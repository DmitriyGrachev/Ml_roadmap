# Pandas core transformations

## Goal

Inspect, filter, group, join, sort, and transform tabular data without hiding its schema.

## Java mental model

Pandas resembles a compact table-processing language more than a Stream pipeline: column operations preserve labels and may align indexes automatically.

## Python model

Use `DataFrame` inspection before transforming it, prefer named aggregations for readable summaries, and make join cardinality explicit.

## Key concepts

CSV ingestion, `loc`, `iloc`, filtering, grouping, named aggregation, joins, sorting, datetimes, and categoricals.

## Example

`example.py` groups synthetic support tickets by channel and gives each output metric a useful name.

## Exercises

Later exercises summarize transactions and validate a merchant join. Their required schema and behavior are deliberately different from this support-ticket example.

## Self-check

1. When should you use `loc` rather than `iloc`?
2. Why are named aggregations easier to maintain?
3. What can an unexpected join expansion indicate?
4. Why inspect dtypes after CSV ingestion?
5. When should a category be stored as a categorical dtype?

## Done when

You can create a sorted grouped summary and state the cardinality you expect from a join.
