"""Saved learner evidence only: this test never starts vLLM or connects to an endpoint."""

import importlib
import os
from pathlib import Path
from statistics import median

import pytest

from roadmap_tools.exercise import exercise_call

protocol = importlib.import_module("labs.05_model_serving.assessment.protocol")
starter = importlib.import_module("labs.05_model_serving.assessment.starter")
pytestmark = pytest.mark.student_exercise


def test_saved_vllm_measurements_and_restart_are_consistent() -> None:
    directory = os.environ.get("ROADMAP_VLLM_EVIDENCE")
    if not directory:
        pytest.skip("NOT_RUN: set ROADMAP_VLLM_EVIDENCE after the actual Linux/vLLM experiment")
    evidence = protocol.load_evidence(Path(directory))
    for name in ("initial", "restarted"):
        run = evidence[name]
        measured = exercise_call(
            starter.summarize_measurements, run["raw"], elapsed_s=run["run_elapsed_s"]
        )
        for field in (
            "requests",
            "completed",
            "errors",
            "completed_requests_per_s",
            "completed_output_tokens_per_s",
        ):
            expected = run["summary"][field]
            if expected is None:
                assert measured[field] is None
            else:
                assert measured[field] == pytest.approx(expected)
        assert measured["latency_ms"]["n"] == run["summary"]["completed"]
        assert measured["error_rate"] == pytest.approx(
            run["summary"]["errors"] / run["summary"]["requests"]
        )
        for output_field, raw_field in (("latency_ms", "e2e_ms"), ("ttft_ms", "ttft_ms")):
            values = [
                row[raw_field]
                for row in run["raw"]
                if row["status"] == "ok" and row[raw_field] is not None
            ]
            actual = measured[output_field]
            assert actual["n"] == len(values)
            assert actual["empirical_p95"] is None  # Existing endpoint batches have at most 8.
            if values:
                assert actual["min"] == pytest.approx(min(values))
                assert actual["median"] == pytest.approx(median(values))
                assert actual["max"] == pytest.approx(max(values))
            else:
                assert actual["min"] is None
                assert actual["median"] is None
                assert actual["max"] is None
