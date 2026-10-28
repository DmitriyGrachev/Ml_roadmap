# Operational signals and service objectives

Read the connected [theory](theory.md) to recalculate the fixed G-01 event window
before implementing the separate request-metrics exercise.

## Goal

Choose observable user outcomes, meaningful denominators, and bounded-cardinality signals
for a library assistant. Connect request latency and failures to explicit service objectives.

## Java mental model

Metrics describe populations; a trace connects stages of one request; a structured event
records a particular occurrence. They answer complementary questions, like endpoint
histograms, distributed spans, and application logs in a backend service.

## Python model

Use a stable request/trace identity for correlation and application-owned release labels.
The example creates span data without installing or exporting telemetry. Actual
[OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/) require instrumentation,
propagation, collection, and storage beyond these local fixtures.

## Key concepts

Track request count, status/reason, latency distributions, provider usage/cost, queue time,
retry attempts, cache outcomes, and quality when labels exist. HTTP success, supported
answers, and safe refusals require different definitions and denominators. Include timeouts
and cancellations in a deliberate policy; surviving completed requests alone can be biased.

Define an SLI (measured indicator), an SLO (target over a stated window), and an error budget
(allowed bad events under that target). Do not confuse a short sample success fraction with
uptime. Define eligible events before choosing thresholds. The SRE
[SLO workbook](https://sre.google/workbook/implementing-slos/) explains this operational framing.

Use route templates, release IDs, and bounded reason codes as metric labels. Raw prompts,
user IDs, full URLs, and request IDs create privacy/cardinality problems; request IDs belong
in appropriately controlled event/trace data. Sampling can bias incident analysis. Never
average p95 values to obtain a global p95, or sum overlapping span durations for request latency.

## Example

```powershell
uv run python modules/08_production_ai/03_observability/example.py
```

Two child spans run concurrently. Their combined durations exceed the request's elapsed
time; the root span records the end-to-end duration.

## Exercises

Complete [Report request reliability and latency](../exercises/request_metrics/README.md).
Its exact success and nearest-rank percentile policies are learning contracts; document
how a real service would also represent requests that never completed.

## Self-check

1. Which denominator makes a success rate interpretable?
2. Where would you record a request ID without making it a metric label?
3. Why can a valid HTTP response still fail a quality indicator?
4. Why is the average of route p95 values not a service-wide p95?
5. What can sampling or missing cancellation events hide?

## Done when

You can read the local report, identify its missing populations, and propose useful metrics,
trace fields, and alerts with explicit measurement windows and owners.
