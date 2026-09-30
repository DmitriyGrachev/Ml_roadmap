"""Student features and actual saved forecasts; TODO remains an expected xfail."""

from pathlib import Path

import pandas as pd
import pytest

from roadmap_tools.exercise import exercise_call

from .evidence import validate_evidence
from .starter import features_at, run_study

pytestmark = pytest.mark.student_exercise


def test_shift_before_rolling_and_earliest_origin() -> None:
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 900], index=pd.date_range("2024-01-01", periods=8))
    origin = pd.Timestamp("2024-01-08")
    row = exercise_call(features_at, series, origin)
    expected = pd.DataFrame(
        {"lag_1": [7.0], "lag_7": [1.0], "rolling_7": [4.0], "day_of_week": [0]},
        index=pd.DatetimeIndex([origin]),
    )
    pd.testing.assert_frame_equal(row, expected, check_dtype=False)


def test_future_mutation_and_truncation_do_not_change_features() -> None:
    series = pd.Series(range(1, 22), index=pd.date_range("2024-01-01", periods=21))
    origin = pd.Timestamp("2024-01-15")
    before = exercise_call(features_at, series, origin)
    changed = series.copy()
    changed.loc[origin:] = 100000
    pd.testing.assert_frame_equal(before, exercise_call(features_at, changed, origin))
    pd.testing.assert_frame_equal(
        before, exercise_call(features_at, series.loc[:"2024-01-14"], origin)
    )


@pytest.mark.parametrize("case", ["too_early", "missing", "too_late", "duplicate", "unsorted"])
def test_invalid_feature_dates(case: str) -> None:
    series = pd.Series(range(1, 11), index=pd.date_range("2024-01-01", periods=10))
    origin = pd.Timestamp("2024-01-08")
    if case == "too_early":
        origin = pd.Timestamp("2024-01-07")
    elif case == "too_late":
        origin = pd.Timestamp("2024-01-12")
    elif case == "missing":
        series = series.drop(pd.Timestamp("2024-01-03"))
    elif case == "duplicate":
        series = pd.concat([series, series.iloc[:1]])
    else:
        series = series.iloc[::-1]
    with pytest.raises(ValueError):  # noqa: PT011 - learner owns error wording
        exercise_call(features_at, series, origin)


def test_actual_study_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "study"
    manifest = exercise_call(run_study, root)
    assert manifest.resolve() == (root / "manifest.json").resolve()
    validate_evidence(root)


def test_preserves_existing_output(tmp_path: Path) -> None:
    marker = tmp_path / "notes.txt"
    marker.write_text("keep")
    with pytest.raises(FileExistsError):
        exercise_call(run_study, tmp_path)
    assert marker.read_text() == "keep"
