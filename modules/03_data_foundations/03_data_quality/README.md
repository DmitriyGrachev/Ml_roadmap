# Data quality checks

## Goal

Measure defects before changing data or trusting a summary. Start with the
[theory companion](theory.md), which traces this lesson's four-document example.
Prerequisite: [Pandas core](../02_pandas_core/README.md) (`data-pandas`),
especially columns, masks, `isna`, and `duplicated`.

## Java mental model

Checking one DTO does not describe a batch. A DataFrame can hold valid and
defective rows together. State what one row and its key mean, then count each
rule explicitly. ID uniqueness differs from comparing every field of a record.

## Python model

Inspect schema and source values first. Build Boolean masks, report their
counts, and only then decide which transformations are justified. In Pandas 3,
Copy-on-Write affects mutation behavior, not the choice of quality policy.

## Key concepts

Row unit, schema, key, missing versus blank and unparseable values, non-finite
numbers, whole-row versus key duplicates, issue versus row counts, audited
conversion, provenance, and mutation policy.

## Example

[`example.py`](example.py) counts repeated document IDs and missing language
metadata in four intake rows. Its exact result is
`{'duplicate_document_ids': 1, 'missing_language': 1}`. The
[worked trace](theory.md#1-сначала-прогноз-потом-отчёт) explains both counts.
Run from the repository root:

```powershell
uv run --offline --no-sync python modules/03_data_foundations/03_data_quality/example.py
```

## Exercises

Try [Transaction quality report](exercises/quality_report/README.md)
(`data-quality-report`): it has a wider transaction schema and independent
invalid-value checks. [Summarize weather observations](../exercises/weather_quality/README.md)
(`data-weather-quality`) counts invalid *rows* before valid duplicate
station/day keys. The teacher document example solves neither student TODO.

Continue with [exploratory data analysis](eda.md) on support tickets, then the
[weather EDA practicum](../exercises/weather_quality/eda_practice.md).

## Self-check

Answer the [seven questions](theory.md#8-проверка-и-перенос) before uncovering
the hints. Explain on a new small input why `isna()` misses a blank string and
why issue counts can exceed the number of bad rows.

## Done when

You can name the row unit and key, reproduce the document counts, distinguish
a repeated key from a repeated whole row, and state whether each report field
counts issues or rows. You can explain where original values and conversion
failures remain visible. Running the teacher example does not change progress.
