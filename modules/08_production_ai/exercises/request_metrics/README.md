# Report request reliability and latency

Difficulty: Medium

## Goal and prerequisites

Turn local request samples into reproducible overall and per-route metrics.
Prerequisites: dataclasses, grouping, sorting, descriptive statistics, and tests.
The full production AI lessons are not required. Estimated time: 45–75 minutes.
Use only supplied in-memory data; no telemetry service or network access is needed.

## Requirements

- A sample has an exact route label, status code, and elapsed latency in
  milliseconds. Route labels must start with `/` and have no outer whitespace;
  they are already normalized, so preserve them exactly.
- Status codes must be integers in inclusive range 100–599, excluding booleans.
  Latencies must be finite nonnegative Python integers or floats, excluding
  booleans; numeric strings are invalid. Raise `ValueError` on invalid samples.
- Compute `Metrics` for all requests and separately for each exact route label.
  A success means `200 <= status_code < 400`; all other statuses are unsuccessful.
  `availability` is successful requests divided by total requests, as a fraction
  from 0 to 1. This is a sample success fraction, not an uptime measurement.
- Use **all** requests, including unsuccessful requests, for mean and p95 latency.
  Mean is the arithmetic mean. P95 uses the nearest-rank definition: sort the
  group's latencies and take the element at one-based position `ceil(0.95 * n)`.
  Do not interpolate or round the results. For 20 latencies from 1 to 20, p95 is 19.
- Return a frozen `RequestReport`; order the tuple of `RouteMetrics`
  lexicographically by route. Counts are integers and statistics are Python floats.
- Empty input returns overall counts of zero, `None` for all three statistics,
  and `routes=()`. A single request has equal mean and p95.
- Do not mutate the input sequence. Repeated calls and input permutations must
  give equivalent statistics (allow normal floating-point tolerance).

## Example

```python
summarize_requests([RequestSample("/search", 200, 100), RequestSample("/search", 503, 300)])
# RequestReport(
#   overall=Metrics(2, 1, 0.5, 200.0, 300.0),
#   routes=(RouteMetrics("/search", Metrics(2, 1, 0.5, 200.0, 300.0)),),
# )
```

## TODO boundary

Implement `summarize_requests` in `starter.py`. Input validation and frozen result
types are supplied. Grouping and metric calculations are intentionally unsolved;
private helpers are allowed.

## Run

```powershell
uv run pytest modules/08_production_ai/exercises/request_metrics -q -rx
```

The unfinished boundary produces expected-incomplete (`xfail`) tests. Completion
means all behavioral tests pass without expected-incomplete results.
