"""Student boundary for an immutable request metrics report."""

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestSample:
    """A completed request with an already normalized route label."""

    route: str
    status_code: int
    latency_ms: float


@dataclass(frozen=True)
class Metrics:
    """Counts, success fraction, and latency statistics for one sample group."""

    total_requests: int
    successful_requests: int
    availability: float | None
    mean_latency_ms: float | None
    p95_latency_ms: float | None


@dataclass(frozen=True)
class RouteMetrics:
    """Statistics for one exact route label."""

    route: str
    metrics: Metrics


@dataclass(frozen=True)
class RequestReport:
    """Overall statistics and route groups ordered by route label."""

    overall: Metrics
    routes: tuple[RouteMetrics, ...]


def summarize_requests(samples: Sequence[RequestSample]) -> RequestReport:
    """Calculate the documented success fraction, mean, and nearest-rank p95."""
    for sample in samples:
        if (
            not isinstance(sample.route, str)
            or not sample.route.startswith("/")
            or sample.route != sample.route.strip()
        ):
            raise ValueError("route must start with / and have no outer whitespace")
        if type(sample.status_code) is not int or not 100 <= sample.status_code <= 599:
            raise ValueError("status_code must be an integer from 100 to 599")
        if (
            type(sample.latency_ms) not in (int, float)
            or not math.isfinite(sample.latency_ms)
            or sample.latency_ms < 0
        ):
            raise ValueError("latency_ms must be a finite nonnegative number")
    # TODO: aggregate overall and per-route counts, availability, mean, and p95.
    raise NotImplementedError("summarize request metrics")
