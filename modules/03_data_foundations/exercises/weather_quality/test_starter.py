"""Quality and aggregation contracts for the weather exercise."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from roadmap_tools.exercise import exercise_call

from .starter import StationSummary, WeatherReport, summarize_weather


def observations(rows: list[list[object]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["station", "day", "temperature_c", "rainfall_mm"])


@pytest.mark.student_exercise
def test_trimmed_keys_keep_first_valid_row_and_group_in_station_order() -> None:
    frame = observations(
        [
            ["South", "2024-02-29", 20, 0],
            [" North ", "2024-02-29", "10", "2.5"],
            ["North", "2024-02-29", 99, 1],
            ["North", "2024-02-29", 40, 8],
            ["North", "2024-03-01", 14, 1.5],
            ["South", "2024-03-01", 22, 3],
        ]
    )
    assert exercise_call(summarize_weather, frame) == WeatherReport(
        total_rows=6,
        invalid_rows=1,
        duplicate_rows=1,
        stations=(StationSummary("North", 2, 12.0, 4.0), StationSummary("South", 2, 21.0, 3.0)),
    )


@pytest.mark.student_exercise
def test_invalid_row_count_is_per_row_and_invalid_rows_do_not_reserve_keys() -> None:
    frame = observations(
        [
            ["North", "2024-01-01", "bad", -1],
            ["North", "2024-01-01", 5, 2],
            ["North", "2024-01-01", 6, 3],
        ]
    )
    assert exercise_call(summarize_weather, frame) == WeatherReport(
        3,
        1,
        1,
        (StationSummary("North", 1, 5.0, 2.0),),
    )


@pytest.mark.student_exercise
@pytest.mark.parametrize(
    "row",
    [
        [None, "2024-01-01", 1, 0],
        [" ", "2024-01-01", 1, 0],
        [7, "2024-01-01", 1, 0],
        ["N", "2023-02-29", 1, 0],
        ["N", "2024-1-01", 1, 0],
        ["N", "2024-01-01T00:00:00", 1, 0],
        ["N", None, 1, 0],
        ["N", "2024-01-01", None, 0],
        ["N", "2024-01-01", float("nan"), 0],
        ["N", "2024-01-01", float("inf"), 0],
        ["N", "2024-01-01", -81, 0],
        ["N", "2024-01-01", 61, 0],
        ["N", "2024-01-01", True, 0],
        ["N", "2024-01-01", 1, -0.1],
        ["N", "2024-01-01", 1, float("inf")],
        ["N", "2024-01-01", 1, "rain"],
        ["N", "2024-01-01", 1, False],
    ],
)
def test_bad_values_count_as_one_invalid_row(row: list[object]) -> None:
    assert exercise_call(summarize_weather, observations([row])) == WeatherReport(1, 1, 0, ())


@pytest.mark.student_exercise
def test_inclusive_temperature_boundaries_extra_columns_and_nonmutation() -> None:
    frame = observations([["Z", "2024-01-01", -80, 0], ["A", "2024-01-01", 60, 0]])
    frame["note"] = ["cold", "hot"]
    frame.index = pd.Index([4, 4])
    before = frame.copy(deep=True)
    report = exercise_call(summarize_weather, frame)
    assert report == WeatherReport(
        2,
        0,
        0,
        (
            StationSummary("A", 1, 60.0, 0.0),
            StationSummary("Z", 1, -80.0, 0.0),
        ),
    )
    assert report == exercise_call(summarize_weather, frame)
    assert_frame_equal(frame, before)


@pytest.mark.student_exercise
def test_empty_frame_with_schema() -> None:
    assert exercise_call(summarize_weather, observations([])) == WeatherReport(0, 0, 0, ())


def test_missing_and_duplicate_column_names() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        exercise_call(summarize_weather, pd.DataFrame({"station": []}))
    frame = pd.DataFrame(columns=["station", "day", "temperature_c", "rainfall_mm", "station"])
    with pytest.raises(ValueError, match="unique"):
        exercise_call(summarize_weather, frame)
