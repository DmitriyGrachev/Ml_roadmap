"""Learner arithmetic, independent of whether a vLLM host is currently available."""

from __future__ import annotations

import importlib

import pytest

from roadmap_tools.exercise import exercise_call

starter = importlib.import_module("labs.05_model_serving.assessment.starter")
pytestmark = pytest.mark.student_exercise


def test_success_error_and_missing_usage_stay_visible() -> None:
    records = [
        {
            "request_index": 0,
            "status": "ok",
            "queue_ms": 0,
            "e2e_ms": 100,
            "ttft_ms": 20,
            "completion_tokens": 4,
        },
        {
            "request_index": 1,
            "status": "deadline",
            "queue_ms": 0,
            "e2e_ms": 500,
            "ttft_ms": None,
            "completion_tokens": None,
        },
        {
            "request_index": 2,
            "status": "ok",
            "queue_ms": 0,
            "e2e_ms": 300,
            "ttft_ms": 60,
            "completion_tokens": 8,
        },
    ]
    result = exercise_call(starter.summarize_measurements, records, elapsed_s=1.0)
    assert result == {
        "requests": 3,
        "completed": 2,
        "errors": 1,
        "error_rate": 1 / 3,
        "completed_requests_per_s": 2.0,
        "completed_output_tokens_per_s": 12.0,
        "latency_ms": {"n": 2, "min": 100.0, "median": 200.0, "max": 300.0, "empirical_p95": None},
        "ttft_ms": {"n": 2, "min": 20.0, "median": 40.0, "max": 60.0, "empirical_p95": None},
    }
    records[0]["completion_tokens"] = None
    unknown = exercise_call(starter.summarize_measurements, records, elapsed_s=1.0)
    assert unknown["completed_output_tokens_per_s"] is None


def test_empirical_percentile_has_declared_minimum_sample_and_nearest_rank() -> None:
    records = [
        {
            "request_index": index,
            "status": "ok",
            "queue_ms": 0,
            "e2e_ms": index + 1,
            "ttft_ms": None,
            "completion_tokens": 1,
        }
        for index in range(20)
    ]
    result = exercise_call(starter.summarize_measurements, records, elapsed_s=1.0)
    assert result["latency_ms"] == {
        "n": 20,
        "min": 1.0,
        "median": 10.5,
        "max": 20.0,
        "empirical_p95": 19.0,
    }
    assert result["ttft_ms"] == {
        "n": 0,
        "min": None,
        "median": None,
        "max": None,
        "empirical_p95": None,
    }


@pytest.mark.parametrize("bad", [float("nan"), -1.0, True])
def test_invalid_duration_is_rejected(bad: float) -> None:
    record = {
        "request_index": 0,
        "status": "ok",
        "queue_ms": 0,
        "e2e_ms": bad,
        "ttft_ms": None,
        "completion_tokens": None,
    }
    with pytest.raises(ValueError, match=r"e2e|duration|finite|number"):
        exercise_call(starter.summarize_measurements, [record], elapsed_s=1.0)


def test_all_failed_is_not_zero_latency_success() -> None:
    record = {
        "request_index": 0,
        "status": "error",
        "queue_ms": 0,
        "e2e_ms": 30,
        "ttft_ms": None,
        "completion_tokens": None,
    }
    result = exercise_call(starter.summarize_measurements, [record], elapsed_s=1.0)
    assert result["completed"] == 0
    assert result["error_rate"] == 1.0
    assert result["completed_output_tokens_per_s"] is None
    assert result["latency_ms"] == {
        "n": 0,
        "min": None,
        "median": None,
        "max": None,
        "empirical_p95": None,
    }
