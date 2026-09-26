"""Behavioral checks for immutable request metrics."""

from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import Metrics, RequestReport, RequestSample, RouteMetrics, summarize_requests


@pytest.mark.student_exercise
def test_overall_and_sorted_route_reports_use_all_latencies() -> None:
    samples = [
        RequestSample("/search", 200, 100),
        RequestSample("/health", 503, 20),
        RequestSample("/search", 302, 300),
        RequestSample("/search", 429, 200),
    ]
    report = exercise_call(summarize_requests, samples)
    assert report.overall == Metrics(4, 2, 0.5, 155.0, 300.0)
    assert report.routes == (
        RouteMetrics("/health", Metrics(1, 0, 0.0, 20.0, 20.0)),
        RouteMetrics("/search", Metrics(3, 2, 2 / 3, 200.0, 300.0)),
    )


@pytest.mark.student_exercise
def test_p95_uses_nearest_rank_without_interpolation() -> None:
    samples = [RequestSample("/a", 200, float(value)) for value in range(20, 0, -1)]
    report = exercise_call(summarize_requests, samples)
    assert report.overall == Metrics(20, 20, 1.0, 10.5, 19.0)
    assert report.routes[0].metrics.p95_latency_ms == 19.0


@pytest.mark.student_exercise
def test_success_boundaries_and_zero_latency() -> None:
    samples = [RequestSample("/", status, 0) for status in (100, 199, 200, 299, 300, 399, 400, 599)]
    assert exercise_call(summarize_requests, samples).overall == Metrics(8, 4, 0.5, 0.0, 0.0)


@pytest.mark.student_exercise
def test_empty_input_and_single_sample() -> None:
    assert exercise_call(summarize_requests, []) == RequestReport(
        Metrics(0, 0, None, None, None), ()
    )
    assert exercise_call(summarize_requests, [RequestSample("/one", 204, 2.5)]) == RequestReport(
        Metrics(1, 1, 1.0, 2.5, 2.5),
        (RouteMetrics("/one", Metrics(1, 1, 1.0, 2.5, 2.5)),),
    )


@pytest.mark.student_exercise
def test_repeatable_without_mutation_and_independent_of_input_order() -> None:
    samples = [RequestSample("/b", 500, 6.5), RequestSample("/a", 200, 1.5)]
    before = samples.copy()
    first = exercise_call(summarize_requests, samples)
    assert first == exercise_call(summarize_requests, samples)
    assert first == exercise_call(summarize_requests, tuple(reversed(samples)))
    assert samples == before


@pytest.mark.parametrize("route", ["", "search", " /search", "/search "])
def test_invalid_route(route: str) -> None:
    with pytest.raises(ValueError, match="route"):
        exercise_call(summarize_requests, [RequestSample(route, 200, 1)])


@pytest.mark.parametrize("status", [99, 600, True, 200.5])
def test_invalid_status(status: object) -> None:
    with pytest.raises(ValueError, match="status_code"):
        exercise_call(summarize_requests, [RequestSample("/a", cast(int, status), 1)])


@pytest.mark.parametrize("latency", [-1, float("nan"), float("inf"), -float("inf"), True, "10"])
def test_invalid_latency(latency: object) -> None:
    with pytest.raises(ValueError, match="latency_ms"):
        exercise_call(summarize_requests, [RequestSample("/a", 200, cast(float, latency))])
