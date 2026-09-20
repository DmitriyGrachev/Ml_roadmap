# NumPy arrays and vectorization

## Goal

Use shapes, dtypes, masks, axes, and broadcasting to express numerical transformations clearly.

## Java mental model

A NumPy array is not a `double[]` or `List<Double>`: it has one dtype and operations are normally applied across the whole array without boxing each value.

## Python model

Create numeric arrays with an explicit dtype, inspect `shape`, and let compatible dimensions broadcast instead of writing nested loops.

## Key concepts

Indexing, boolean masks, `reshape`, axes, aggregation, broadcasting, dot products, and vectorization.

## Example

`example.py` reshapes two support SLA thresholds into a column and broadcasts a comparison across four response times, producing a boolean compliance matrix.

## Exercises

The later payment-matrix exercise asks you to validate and scale a caller-provided amount matrix. It uses a different operation and shape contract from this fixed comparison example.

## Self-check

1. What does an array shape `(2, 3)` describe?
2. Why should a numeric dtype be explicit?
3. Which dimensions must align for broadcasting?
4. What does `axis=0` aggregate over?
5. When is a boolean mask more readable than index arithmetic?

## Done when

You can predict the shape of a broadcasted result and explain why no Python loop is required.
