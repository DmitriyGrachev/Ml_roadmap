"""Acceptance tests for the chronological-split student boundary."""

from __future__ import annotations

import pandas as pd
import pytest

from roadmap_tools import exercise_call

from .starter import chronological_split


def _independence_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transaction_id": ["T-6", "T-1", "T-5", "T-2", "T-4", "T-3"],
            "amount": [60.0, 10.0, 50.0, 20.0, 40.0, 30.0],
            "timestamp": pd.to_datetime(
                [
                    "2026-01-06T00:00:00Z",
                    "2026-01-01T00:00:00Z",
                    "2026-01-05T00:00:00Z",
                    "2026-01-02T00:00:00Z",
                    "2026-01-04T00:00:00Z",
                    "2026-01-03T00:00:00Z",
                ],
                utc=True,
            ),
        }
    )


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


def test_accepts_zero_validation_fraction() -> None:
    frame = _independence_frame()

    train, validation, test = exercise_call(chronological_split, frame, 0.5, 0.0)

    assert len(train) == 3
    assert validation.empty
    assert len(test) == 3


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


@pytest.mark.parametrize("partition_index", [0, 1, 2], ids=["train", "validation", "test"])
def test_mutating_each_returned_partition_does_not_change_source(
    partition_index: int,
) -> None:
    frame = _independence_frame()
    original = frame.copy(deep=True)
    partitions = exercise_call(chronological_split, frame, 0.34, 0.34)

    mutated = partitions[partition_index]
    mutated.at[mutated.index[0], "amount"] = -999.0

    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize("partition_index", [0, 1, 2], ids=["train", "validation", "test"])
def test_mutating_one_returned_partition_does_not_change_the_others(
    partition_index: int,
) -> None:
    partitions = exercise_call(chronological_split, _independence_frame(), 0.34, 0.34)
    originals = tuple(partition.copy(deep=True) for partition in partitions)

    mutated = partitions[partition_index]
    mutated.at[mutated.index[0], "amount"] = -999.0

    for other_index in {0, 1, 2}.difference({partition_index}):
        pd.testing.assert_frame_equal(partitions[other_index], originals[other_index])


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

    train, validation, test = exercise_call(chronological_split, frame, 0.4, 0.4)

    assert train["timestamp"].max() <= validation["timestamp"].min()
    assert validation["timestamp"].max() <= test["timestamp"].min()


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
