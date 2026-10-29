"""Offline contracts complement (and cannot replace) the explicit TCP run."""

import math
import urllib.error
import urllib.request

import pytest

from . import demo
from .transport import request


def test_summary_counts_every_outcome_and_uses_success_latencies_only() -> None:
    rows = [
        {"outcome": "ok", "seconds": 0.2},
        {"outcome": "ok", "seconds": 0.4},
        {"outcome": "http_error", "seconds": 0.1},
        {"outcome": "timeout", "seconds": 1.0},
        {"outcome": "transport_error", "seconds": 0.5},
    ]
    result = demo.summarize(rows)
    assert result["attempts"] == 5
    assert result["successes"] == 2
    assert result["timeouts"] == 1
    assert result["failures"] == 3
    assert result["median_seconds"] == pytest.approx(0.3)
    assert result["observed_max_seconds"] == 0.4
    assert demo.summarize([])["median_seconds"] is None


def test_timeout_is_counted_without_claiming_server_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        raise urllib.error.URLError(TimeoutError("deadline"))

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", timeout)
    result = request("http://127.0.0.1:1/predict", {"text": "triangle"}, timeout=0.01)
    assert result["outcome"] == "timeout"
    assert result["status"] is None


def test_monitoring_waits_for_labels_and_does_not_infer_quality_from_drift() -> None:
    predictions = [
        {"request_id": "a", "prediction": "circle", "predicted_at": 10},
        {"request_id": "b", "prediction": "triangle", "predicted_at": 20},
    ]
    labels = [
        {"request_id": "a", "label": "triangle", "available_at": 50},
        {"request_id": "b", "label": "triangle", "available_at": 100},
    ]
    early = demo.delayed_quality(predictions, labels, as_of=30)
    assert early == {"labeled_count": 0, "coverage": 0.0, "accuracy": None}
    late = demo.delayed_quality(predictions, labels, as_of=60)
    assert late == {"labeled_count": 1, "coverage": 0.5, "accuracy": 0.0}


@pytest.mark.parametrize("value", [float("nan"), -1.0, float("inf")])
def test_summary_rejects_invalid_durations(value: float) -> None:
    assert not math.isfinite(value) or value < 0
    with pytest.raises(ValueError, match="invalid measured"):
        demo.summarize([{"outcome": "ok", "seconds": value}])
