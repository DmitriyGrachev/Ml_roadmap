"""The synthetic worked arithmetic is not a benchmark."""

from importlib import import_module

import pytest


def test_overlapping_request_time_does_not_replace_wall_time() -> None:
    example = import_module("labs.05_model_serving.assessment.example").worked_example()
    assert example["origin"] == "SYNTHETIC_ARITHMETIC_ONLY"
    assert example["successful_requests_per_s"] == 15
    assert example["median_success_latency_ms"] == 120
    assert example["sum_request_durations_s"] == pytest.approx(0.36)
    assert example["batch_wall_s"] == pytest.approx(0.2)
    assert example["empirical_p95"] is None
