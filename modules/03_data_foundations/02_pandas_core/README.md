# Pandas core transformations

## Goal

Inspect, filter, group, join, sort, and transform tabular data without hiding its schema.

Start with [the theory companion](theory.md): it explains why labels, missing values,
and join keys change results. Prerequisites: [Python collections](../../01_python_core/02_collections/README.md)
and [NumPy arrays](../01_numpy/README.md) (`data-numpy`).

## Java mental model

Pandas resembles a compact table-processing language more than a Stream pipeline: column operations preserve labels and may align indexes automatically.
The [companion](theory.md) uses small neutral tables to make that alignment visible.

## Python model

Use `DataFrame` inspection before transforming it, prefer named aggregations for readable summaries, and make join cardinality explicit.
Read a column as a labeled `Series`, not merely as an array of values.

## Key concepts

CSV ingestion, `loc`, `iloc`, filtering, grouping, named aggregation, joins, sorting, datetimes, and categoricals.
The companion also covers `Index`, label alignment, nulls, duplicate policies,
`size` versus `count`, `dropna`, `observed`, and Pandas 3 Copy-on-Write.

## Example

`example.py` groups synthetic support tickets by channel and gives each output metric a useful name.
The [worked explanation](theory.md#7-группы-и-именованные-агрегаты) walks through its
input, each operation, and exact result. Run it from the repository root:

```powershell
uv run python modules/03_data_foundations/02_pandas_core/example.py
```

## Exercises

Later exercises summarize transactions and validate a merchant join. Their required schema and behavior are deliberately different from this support-ticket example.
After the companion, try [Transaction summary](exercises/transaction_summary/README.md)
(`data-transaction-summary`) for grouped output and
[Merchant risk join](exercises/merchant_join/README.md) (`data-merchant-join`)
for cardinality checks. The [Pandas notebook](../notebooks/README.md) offers another
practice route. Continue with [data quality](../03_data_quality/README.md)
(`data-quality`) once you can state a missing-value and duplicate policy.

## Self-check

First answer the [eight questions in the companion](theory.md#11-самопроверка),
then uncover its answers. In particular, explain a label-alignment result and
predict the row count of a many-to-many merge before running code.

## Done when

You can create a sorted grouped summary; distinguish label from position; choose
explicit missing, duplicate, and dtype policies; and state the cardinality you
expect from a join before running it.
