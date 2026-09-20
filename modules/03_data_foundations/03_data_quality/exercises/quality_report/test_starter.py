"""Acceptance tests for the data-quality student boundary."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pandas as pd
import pytest

from roadmap_tools import exercise_call  # type: ignore[import-untyped]

from .starter import QualityReport, assess_transaction_quality


def test_reports_clean_transaction_data() -> None:
    clean = pd.DataFrame(
        {
            "id": ["T-1", "T-2"],
            "amount": ["10.00", "20.50"],
            "timestamp": ["2026-01-01T10:00:00Z", "2026-01-02T10:00:00Z"],
            "category": ["food", "travel"],
        }
    )

    report = exercise_call(assess_transaction_quality, clean)

    assert report == QualityReport(
        missing_id_count=0,
        duplicate_id_count=0,
        invalid_amount_count=0,
        invalid_timestamp_count=0,
        unknown_category_count=0,
    )


def test_accepts_timezone_aware_values_with_non_utc_offsets() -> None:
    frame = pd.DataFrame(
        {
            "id": ["T-1", "T-2"],
            "amount": [10.0, 20.0],
            "timestamp": [
                "2026-01-01T10:00:00+02:00",
                pd.Timestamp("2026-01-02T10:00:00-04:00"),
            ],
        }
    )

    report = exercise_call(assess_transaction_quality, frame)

    assert report == QualityReport(
        missing_id_count=0,
        duplicate_id_count=0,
        invalid_amount_count=0,
        invalid_timestamp_count=0,
        unknown_category_count=0,
    )


def test_reports_overlapping_quality_defects_without_mutating_input() -> None:
    frame = pd.DataFrame(
        {
            "id": [None, None, "   ", "T-2", "T-2", "T-5", "T-6", "T-7"],
            "amount": [
                "10.00",
                "11.00",
                "not-a-number",
                "5.00",
                None,
                "-3",
                "0",
                float("inf"),
            ],
            "timestamp": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T10:00:00Z",
                "not-a-timestamp",
                "2026-01-03T10:00:00Z",
                "2026-01-04T10:00:00",
                "2026-01-05T10:00:00Z",
                None,
                "2026-01-07T10:00:00Z",
            ],
            "category": [
                "food",
                "travel",
                "unknown",
                "travel",
                None,
                "other",
                "utilities",
                "food",
            ],
        }
    )
    original = frame.copy(deep=True)

    report = exercise_call(assess_transaction_quality, frame)

    assert report == QualityReport(
        missing_id_count=3,
        duplicate_id_count=1,
        invalid_amount_count=5,
        invalid_timestamp_count=3,
        unknown_category_count=2,
    )
    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize("category", [None, pd.Series([None, None], dtype="object")])
def test_treats_an_absent_or_all_missing_optional_category_as_known(
    category: pd.Series | None,
) -> None:
    data: dict[str, object] = {
        "id": ["T-1", "T-2"],
        "amount": [10.0, 20.0],
        "timestamp": ["2026-01-01T10:00:00Z", "2026-01-02T10:00:00Z"],
    }
    if category is not None:
        data["category"] = category
    frame = pd.DataFrame(data)

    report = exercise_call(assess_transaction_quality, frame)

    assert report == QualityReport(
        missing_id_count=0,
        duplicate_id_count=0,
        invalid_amount_count=0,
        invalid_timestamp_count=0,
        unknown_category_count=0,
    )


def test_rejects_missing_required_columns_without_using_expected_incomplete() -> None:
    with pytest.raises(ValueError, match="required"):
        assess_transaction_quality(pd.DataFrame({"id": ["T-1"], "amount": [10.0]}))


def test_quality_report_has_the_documented_immutable_schema() -> None:
    assert [field.name for field in fields(QualityReport)] == [
        "missing_id_count",
        "duplicate_id_count",
        "invalid_amount_count",
        "invalid_timestamp_count",
        "unknown_category_count",
    ]
    report = QualityReport(0, 0, 0, 0, 0)
    field_name = "missing_id_count"

    with pytest.raises(FrozenInstanceError):
        setattr(report, field_name, 1)
