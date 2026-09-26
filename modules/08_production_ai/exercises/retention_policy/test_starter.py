"""Choose expired records without touching storage or bypassing legal holds."""

# ruff: noqa: PT011 -- The public contract specifies exception classes, not message text.

from datetime import UTC, datetime, timedelta, timezone
from typing import cast

import pytest

from roadmap_tools import exercise_call

from .starter import RetentionRecord, plan_retention

NOW = datetime(2026, 6, 20, 12, tzinfo=UTC)
CUTOFF = datetime(2026, 6, 10, 12, tzinfo=UTC)


def test_only_records_strictly_before_cutoff_are_candidates() -> None:
    records = (
        RetentionRecord("old", CUTOFF - timedelta(microseconds=1), False),
        RetentionRecord("boundary", CUTOFF, False),
        RetentionRecord("new", CUTOFF + timedelta(microseconds=1), False),
    )
    assert exercise_call(plan_retention, records, NOW, 10) == ("old",)
    assert records[1] == RetentionRecord("boundary", CUTOFF, False)


def test_legal_hold_protects_even_the_oldest_record() -> None:
    records = (
        RetentionRecord("held", NOW - timedelta(days=100), True),
        RetentionRecord("free", NOW - timedelta(days=11), False),
    )
    assert exercise_call(plan_retention, records, NOW, 10) == ("free",)


def test_candidates_sort_by_instant_then_id_not_input_order() -> None:
    records = (
        RetentionRecord("b", NOW - timedelta(days=11), False),
        RetentionRecord("a", NOW - timedelta(days=11), False),
        RetentionRecord("z", NOW - timedelta(days=12), False),
    )
    assert exercise_call(plan_retention, records, NOW, 10) == ("z", "a", "b")
    assert tuple(record.record_id for record in records) == ("b", "a", "z")


def test_compares_absolute_instants_across_timezone_offsets() -> None:
    east = timezone(timedelta(hours=3))
    records = (
        RetentionRecord("same-cutoff", datetime(2026, 6, 10, 15, tzinfo=east), False),
        RetentionRecord("old", datetime(2026, 6, 10, 14, 59, tzinfo=east), False),
    )
    assert exercise_call(plan_retention, records, NOW.astimezone(east), 10) == ("old",)


def test_empty_input_returns_no_candidates() -> None:
    assert exercise_call(plan_retention, (), NOW, 10) == ()


def test_future_record_is_invalid_even_under_legal_hold() -> None:
    with pytest.raises(ValueError):
        exercise_call(
            plan_retention, (RetentionRecord("future", NOW + timedelta(seconds=1), True),), NOW, 10
        )


@pytest.mark.parametrize("days", [0, -1, True, 36501])
def test_rejects_invalid_retention_days(days: int) -> None:
    with pytest.raises(ValueError):
        exercise_call(plan_retention, (), NOW, days)


def test_naive_reference_time_is_rejected() -> None:
    with pytest.raises(ValueError):
        exercise_call(plan_retention, (), NOW.replace(tzinfo=None), 10)


def test_naive_record_time_is_rejected_even_under_hold() -> None:
    with pytest.raises(ValueError):
        exercise_call(
            plan_retention, (RetentionRecord("a", CUTOFF.replace(tzinfo=None), True),), NOW, 10
        )


@pytest.mark.parametrize("record_id", ["", " a", "a ", "a" * 81])
def test_invalid_record_id_is_rejected(record_id: str) -> None:
    with pytest.raises(ValueError):
        exercise_call(plan_retention, (RetentionRecord(record_id, CUTOFF, False),), NOW, 10)


def test_duplicate_ids_are_rejected_before_candidate_selection() -> None:
    with pytest.raises(ValueError):
        exercise_call(
            plan_retention,
            (
                RetentionRecord("a", CUTOFF, True),
                RetentionRecord("a", CUTOFF - timedelta(days=1), False),
            ),
            NOW,
            10,
        )


def test_hold_flag_must_be_boolean() -> None:
    with pytest.raises(ValueError):
        exercise_call(plan_retention, (RetentionRecord("a", CUTOFF, cast(bool, 0)),), NOW, 10)


def test_unrepresentable_cutoff_raises_value_error() -> None:
    with pytest.raises(ValueError):
        exercise_call(plan_retention, (), datetime(1, 1, 1, tzinfo=UTC), 1)
