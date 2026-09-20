"""Acceptance tests for the transaction-summary student boundary."""

from __future__ import annotations

import pandas as pd
import pytest

from roadmap_tools import exercise_call

from .starter import summarize_transactions


def test_summarizes_observed_categorical_groups_in_deterministic_order() -> None:
    frame = pd.DataFrame(
        {
            "currency": pd.Categorical(["USD", "EUR", "USD"], categories=["EUR", "GBP", "USD"]),
            "status": pd.Categorical(
                ["settled", "declined", "settled"], categories=["declined", "settled"]
            ),
            "amount": [10.0, 20.0, 30.0],
            "timestamp": ["2026-01-03T10:00:00Z", "2026-01-01T10:00:00Z", "2026-01-02T10:00:00Z"],
        }
    )
    original = frame.copy(deep=True)

    summary = exercise_call(summarize_transactions, frame)

    expected = pd.DataFrame(
        {
            "currency": pd.Series(["EUR", "USD"], dtype="string"),
            "status": pd.Series(["declined", "settled"], dtype="string"),
            "transaction_count": pd.Series([1, 2], dtype="int64"),
            "total_amount": pd.Series([20.0, 40.0], dtype="float64"),
            "median_amount": pd.Series([20.0, 20.0], dtype="float64"),
            "p95_amount": pd.Series([20.0, 29.0], dtype="float64"),
        }
    )
    pd.testing.assert_frame_equal(summary, expected, check_exact=False, rtol=1e-9, atol=1e-9)
    pd.testing.assert_frame_equal(frame, original)


def test_excludes_rows_missing_a_grouping_value_or_amount() -> None:
    frame = pd.DataFrame(
        {
            "currency": ["USD", None, "USD", "EUR", "GBP"],
            "status": ["settled", "settled", None, "declined", "settled"],
            "amount": [10.0, 20.0, None, 30.0, 40.0],
            "timestamp": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T10:00:00Z",
                "2026-01-03T10:00:00Z",
                "2026-01-04T10:00:00Z",
                None,
            ],
        }
    )

    summary = exercise_call(summarize_transactions, frame)

    expected = pd.DataFrame(
        {
            "currency": pd.Series(["EUR", "USD"], dtype="string"),
            "status": pd.Series(["declined", "settled"], dtype="string"),
            "transaction_count": pd.Series([1, 1], dtype="int64"),
            "total_amount": pd.Series([30.0, 10.0], dtype="float64"),
            "median_amount": pd.Series([30.0, 10.0], dtype="float64"),
            "p95_amount": pd.Series([30.0, 10.0], dtype="float64"),
        }
    )
    pd.testing.assert_frame_equal(summary, expected, check_exact=False, rtol=1e-9, atol=1e-9)


@pytest.mark.parametrize(
    ("frame", "message"),
    [
        (pd.DataFrame({"currency": ["USD"]}), "missing required columns"),
        (
            pd.DataFrame(
                {
                    "currency": ["USD"],
                    "status": ["settled"],
                    "amount": [1.0],
                    "timestamp": ["not-a-timestamp"],
                }
            ),
            "timestamp values must be parseable",
        ),
    ],
)
def test_rejects_missing_required_columns_or_unparseable_timestamps(
    frame: pd.DataFrame, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        summarize_transactions(frame)
