# Module 03 — Data foundations

## Goal

Build the data literacy needed to inspect AI inputs, make defensible claims, and evaluate a classifier beyond a single headline score.

## Java mental model

NumPy and Pandas are not Java collection libraries: their useful operations describe whole columns or arrays at once rather than iterating object by object.

## Python model

Work through the lessons in order, run each `example.py`, then use the later exercises to implement the same mechanics on separate synthetic payment data.

## Key concepts

Arrays, tabular transformations, quality checks, descriptive statistics, temporal splits, and imbalanced-class metrics form one workflow.

## Example

Run a lesson from the repository root:

```powershell
uv run python modules/03_data_foundations/01_numpy/example.py
```

## Exercises

Exercises arrive alongside their lessons. Keep examples as reference for mechanics, not as implementations to copy into a starter boundary.

## Self-check

1. Why can vectorized work be clearer than a loop?
2. What is the difference between a missing value and a duplicate row?
3. Why does correlation not establish causation?
4. Why must a time-based split be ordered?
5. When can accuracy be misleading?

## Done when

You can explain the purpose of each lesson and run its deterministic example without changing tracked data.
