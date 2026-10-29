"""Poisoned future, query identity, UTC validation and empty-history contracts."""

from typing import Any

import numpy as np
import pandas as pd
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import build_point_in_time_features

pytestmark = pytest.mark.student_exercise


def fixtures() -> tuple[pd.DataFrame, pd.DataFrame]:
    events = pd.DataFrame(
        {
            "event_id": ["future", "right", "b", "inside2", "left", "inside1", "old"],
            "entity_id": ["a", "a", "b", "a", "a", "a", "a"],
            "event_time": pd.to_datetime(
                [
                    "2026-02-06",
                    "2026-02-05",
                    "2026-02-04",
                    "2026-02-04",
                    "2026-02-03",
                    "2026-02-04",
                    "2026-02-02",
                ],
                utc=True,
            ),
            "amount": [1e12, 1e10, 30.0, 7.0, 2.0, -1.0, 1e8],
        },
        index=[70, 60, 50, 40, 30, 20, 10],
    )
    queries = pd.DataFrame(
        {
            "query_id": ["late", "b-query", "unknown", "early", "no-history"],
            "entity_id": ["a", "b", "missing", "a", "a"],
            "as_of": pd.to_datetime(
                ["2026-02-05", "2026-02-05", "2026-02-05", "2026-02-04", "2026-01-01"],
                utc=True,
            ),
        },
        index=[91, 12, 37, 8, 6],
    )
    return events, queries


def test_temporal_edges_duplicate_times_entities_and_query_identity() -> None:
    events, queries = fixtures()
    before_events, before_queries = events.copy(deep=True), queries.copy(deep=True)
    actual = exercise_call(build_point_in_time_features, events, queries, pd.Timedelta(days=2))
    expected = pd.DataFrame(
        {
            "query_id": queries["query_id"].tolist(),
            "count": [3, 1, 0, 2, 0],
            "sum": [8.0, 30.0, 0.0, 100000002.0, 0.0],
            "mean": [8 / 3, 30.0, np.nan, 50000001.0, np.nan],
        }
    )
    pd.testing.assert_frame_equal(actual, expected)
    pd.testing.assert_frame_equal(events, before_events)
    pd.testing.assert_frame_equal(queries, before_queries)
    shuffled = exercise_call(
        build_point_in_time_features,
        events.sample(frac=1, random_state=5),
        queries,
        pd.Timedelta(days=2),
    )
    pd.testing.assert_frame_equal(actual, shuffled)


def test_future_poison_cannot_change_existing_answers() -> None:
    events, queries = fixtures()
    baseline = exercise_call(build_point_in_time_features, events, queries, pd.Timedelta(days=2))
    events.loc[events["event_id"].eq("future"), "amount"] = -9e15
    events.loc[events["event_id"].eq("right"), "amount"] = 8e15
    actual = exercise_call(build_point_in_time_features, events, queries, pd.Timedelta(days=2))
    pd.testing.assert_frame_equal(actual, baseline)


def test_empty_events_and_empty_queries_keep_schema() -> None:
    events, queries = fixtures()
    actual = exercise_call(
        build_point_in_time_features, events.iloc[:0], queries, pd.Timedelta(seconds=1)
    )
    assert actual["query_id"].tolist() == queries["query_id"].tolist()
    assert actual["count"].tolist() == [0] * len(queries)
    assert actual["sum"].tolist() == [0.0] * len(queries)
    assert actual["mean"].isna().all()
    empty = exercise_call(
        build_point_in_time_features, events, queries.iloc[:0], pd.Timedelta(seconds=1)
    )
    assert empty.empty
    assert empty.columns.tolist() == ["query_id", "count", "sum", "mean"]
    assert [str(dtype) for dtype in empty.dtypes] == ["object", "int64", "float64", "float64"]


@pytest.mark.parametrize("window", [pd.Timedelta(0), pd.Timedelta(days=-1), pd.NaT, "2D"])
def test_invalid_window(window: Any) -> None:
    events, queries = fixtures()
    with pytest.raises(ValueError, match=r"."):
        exercise_call(build_point_in_time_features, events, queries, window)


@pytest.mark.parametrize("table", ["events", "queries"])
@pytest.mark.parametrize(
    "problem",
    [
        "duplicate_id",
        "missing_id",
        "empty_id",
        "missing_entity",
        "naive",
        "non_utc",
        "mixed",
        "nat",
        "missing_column",
    ],
)
def test_invalid_schema_and_timestamps(table: str, problem: str) -> None:
    events, queries = fixtures()
    frame = events if table == "events" else queries
    identifier = "event_id" if table == "events" else "query_id"
    time = "event_time" if table == "events" else "as_of"
    if problem == "duplicate_id":
        frame.loc[frame.index[0], identifier] = frame[identifier].iloc[1]
    elif problem == "missing_id":
        frame.loc[frame.index[0], identifier] = None
    elif problem == "empty_id":
        frame.loc[frame.index[0], identifier] = ""
    elif problem == "missing_entity":
        frame.loc[frame.index[0], "entity_id"] = None
    elif problem == "naive":
        frame[time] = frame[time].dt.tz_localize(None)
    elif problem == "non_utc":
        frame[time] = frame[time].dt.tz_convert("Europe/Berlin")
    elif problem == "mixed":
        frame[time] = frame[time].astype(object)
        frame.loc[frame.index[0], time] = pd.Timestamp("2026-02-03")
    elif problem == "nat":
        frame.loc[frame.index[0], time] = pd.NaT
    else:
        frame.drop(columns=identifier, inplace=True)
    with pytest.raises(ValueError, match=r"."):
        exercise_call(build_point_in_time_features, events, queries, pd.Timedelta(days=2))


@pytest.mark.parametrize("amount", [np.nan, np.inf, -np.inf, "bad"])
def test_invalid_amount_even_on_future_rows(amount: Any) -> None:
    events, queries = fixtures()
    events["amount"] = events["amount"].astype(object)
    events.loc[events.index[0], "amount"] = amount
    with pytest.raises(ValueError, match=r"."):
        exercise_call(build_point_in_time_features, events, queries, pd.Timedelta(days=2))
