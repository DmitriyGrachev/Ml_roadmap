"""Acceptance tests for the chronological-split student boundary."""

from __future__ import annotations

import pandas as pd
import pytest

from roadmap_tools import exercise_call

from .starter import chronological_split


def test_sorts_chronologically_and_uses_floor_partition_sizes() -> None:
    frame = pd.DataFrame(
        {
            "transaction_id": ["T-7", "T-2", "T-5", "T-1", "T-6", "T-4", "T-3"],
            "timestamp": pd.to_datetime(
                [
                    "2026-01-07T00:00:00Z",
                    "2026-01-02T00:00:00Z",
                    "2026-01-05T00:00:00Z",
                    "2026-01-01T00:00:00Z",
                    "2026-01-06T00:00:00Z",
                    "2026-01-04T00:00:00Z",
                    "2026-01-03T00:00:00Z",
                ],
                utc=True,
            ),
        }
    )

    train, validation, test = exercise_call(chronological_split, frame, 0.5, 0.25)

    assert train["transaction_id"].tolist() == ["T-1", "T-2", "T-3"]
    assert validation["transaction_id"].tolist() == ["T-4"]
    assert test["transaction_id"].tolist() == ["T-5", "T-6", "T-7"]


def test_does_not_mutate_the_caller_owned_frame() -> None:
    frame = pd.DataFrame(
        {
            "transaction_id": ["later", "earlier"],
            "timestamp": pd.to_datetime(["2026-01-02T00:00:00Z", "2026-01-01T00:00:00Z"], utc=True),
        }
    )
    original = frame.copy(deep=True)

    exercise_call(chronological_split, frame, 0.5, 0.25)

    pd.testing.assert_frame_equal(frame, original)


def test_preserves_input_order_for_duplicate_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "transaction_id": ["same-first", "later", "same-second", "earlier"],
            "timestamp": pd.to_datetime(
                [
                    "2026-01-02T00:00:00Z",
                    "2026-01-03T00:00:00Z",
                    "2026-01-02T00:00:00Z",
                    "2026-01-01T00:00:00Z",
                ],
                utc=True,
            ),
        }
    )

    train, validation, test = exercise_call(chronological_split, frame, 0.25, 0.5)

    combined_ids = pd.concat([train, validation, test])["transaction_id"].tolist()
    assert combined_ids == ["earlier", "same-first", "same-second", "later"]


def test_never_places_a_later_row_before_an_earlier_partition() -> None:
    frame = pd.DataFrame(
        {
            "transaction_id": ["T-4", "T-1", "T-5", "T-2", "T-3"],
            "timestamp": pd.to_datetime(
                [
                    "2026-01-04T00:00:00Z",
                    "2026-01-01T00:00:00Z",
                    "2026-01-05T00:00:00Z",
                    "2026-01-02T00:00:00Z",
                    "2026-01-03T00:00:00Z",
                ],
                utc=True,
            ),
        }
    )

    train, validation, test = exercise_call(chronological_split, frame, 0.4, 0.2)

    assert train["timestamp"].max() <= validation["timestamp"].min()
    assert validation["timestamp"].min() <= test["timestamp"].min()


@pytest.mark.parametrize(
    ("train_fraction", "validation_fraction"),
    [
        (0.0, 0.2),
        (1.0, 0.0),
        (-0.1, 0.2),
        (0.5, -0.1),
        (0.5, 1.0),
        (0.8, 0.2),
        (0.8, 0.3),
    ],
)
def test_rejects_invalid_partition_fractions(
    train_fraction: float,
    validation_fraction: float,
) -> None:
    frame = pd.DataFrame({"timestamp": pd.to_datetime(["2026-01-01T00:00:00Z"], utc=True)})

    with pytest.raises(ValueError, match=r"fraction|sum"):
        exercise_call(chronological_split, frame, train_fraction, validation_fraction)
