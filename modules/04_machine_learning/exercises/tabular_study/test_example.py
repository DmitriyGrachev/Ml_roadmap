"""CPU-only fixture and serialization checks, separate from ML evaluation."""

import json
from pathlib import Path

import pandas as pd
import pytest

from .example import run_sensor_lifecycle
from .fixture import make_fixture


def test_sensor_ensembles_expose_averaging_and_sequential_stages() -> None:
    from . import example

    report = example.compare_sensor_ensembles(seed=11)
    assert report == example.compare_sensor_ensembles(seed=11)
    assert report["train_count"] == 64
    assert report["validation_count"] == 16
    assert report["forest_trees"] == 8
    assert report["boosting_stages"] == 8
    assert report["forest_average_error"] < 1e-12
    assert report["forest_disagreement"] > 0
    for family in ("tree", "forest", "boosting"):
        probabilities = report["probabilities"][family]
        assert len(probabilities) == 16
        assert all(0 <= value <= 1 for value in probabilities)
    assert len(report["boosting_validation_brier"]) == 8


def test_fixture_has_repeatable_grouped_support_records() -> None:
    frame = make_fixture(13)
    pd.testing.assert_frame_equal(frame, make_fixture(13))
    assert not frame.equals(make_fixture(14))
    assert 60 <= len(frame) <= 300
    assert frame["row_id"].is_unique
    assert frame["group_id"].nunique() < len(frame)
    assert set(frame["outcome"]) == {0, 1}
    assert {"time_id", "channel", "message_length", "prior_contacts", "queue_minutes"} <= set(frame)
    assert frame["message_length"].isna().any()


def test_sensor_lifecycle_persists_actual_probabilities_without_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "sensor"
    report_path = run_sensor_lifecycle(root, seed=11)
    report = json.loads(report_path.read_text())
    assert report["case"] == "sensor-maintenance"
    assert report["replayed"] is True
    assert len(report["probabilities"]) == 8
    assert all(0 <= p <= 1 for p in report["probabilities"])
    assert len(set(report["probabilities"])) > 1
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    with pytest.raises(FileExistsError):
        run_sensor_lifecycle(root, seed=11)
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}
