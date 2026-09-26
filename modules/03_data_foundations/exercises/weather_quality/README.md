# Summarize weather observations

Difficulty: Medium

## Goal and prerequisites

Produce an immutable quality report and station summaries from a Pandas table.
Prerequisites: Pandas selection, numeric conversion, missing values, grouping,
and data-quality lessons 02–04. Estimated time: 60–90 minutes.

## Requirements

- Require unique column names and columns `station`, `day`, `temperature_c`,
  `rainfall_mm`; raise `ValueError` for a missing required column or repeated
  column name. Extra columns and arbitrary, even repeated, index labels are allowed.
- A station must be a string that remains nonempty after trimming outer
  whitespace. Group by this trimmed, case-sensitive name.
- A day must be a string in exact `YYYY-MM-DD` format naming a valid calendar
  date. Do not accept timestamps, surrounding whitespace, or single-digit months.
- Temperature and rainfall may be numbers or numeric strings. Both must convert
  to finite numbers; booleans, missing values, and unparseable values are invalid.
  Temperature must be in inclusive range `[-80, 60]`; rainfall must be at least zero.
- Count each row failing one or more checks once in `invalid_rows`, then discard
  it. Among remaining valid rows, keep the first occurrence of each normalized
  `(station, day)` pair in input order. Count later occurrences in `duplicate_rows`.
  Invalid rows must not reserve a key or count as duplicates.
- For retained rows, produce each station's observation count, arithmetic mean
  temperature, and sum of rainfall. Use Python floats, without rounding. Sort
  the `stations` tuple lexicographically by normalized station name.
- Include all original rows in `total_rows`. Empty input with the required columns
  returns zero counts and `stations=()`. Do not mutate input data, index, or dtypes.

## Example

```text
station  day         temperature_c  rainfall_mm
North    2024-01-01  10             2
North    2024-01-01  20             7
North    2024-01-02  14             0
South    2024-01-01  bad            1
```

Expected result:

```python
WeatherReport(
    total_rows=4,
    invalid_rows=1,
    duplicate_rows=1,
    stations=(StationSummary("North", 2, 12.0, 2.0),),
)
```

## TODO boundary

Implement `summarize_weather` in `starter.py`. Column validation and frozen result
types are provided; value validation, deduplication, and aggregation are your work.
Private helpers are allowed. Do not add a completed solution beside the starter.

## Run

```powershell
uv run pytest modules/03_data_foundations/exercises/weather_quality -q -rx
```

Behavioral tests are expected incomplete (`xfail`) until implemented. Completion
means all behavioral tests pass without expected-incomplete results.
