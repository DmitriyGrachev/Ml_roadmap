"""Behavior checks for sensor-group isolation and deterministic assignment."""

import numpy as np
import pandas as pd
import pytest

from roadmap_tools import exercise_call

from .starter import split_sensor_groups


def observations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sensor": ["F", "A", "C", "B", "A", "E", "D", "C", "F", "F"],
            "reading": list(range(10)),
        },
        index=[8, 8, 3, 3, 1, 1, 4, 4, 0, 0],
    )


def test_group_membership_and_original_row_order() -> None:
    frame = observations()
    train, validation, test = exercise_call(split_sensor_groups, frame, "sensor", 0.5, 0.2, 42)

    # Seed 42 permutes sorted labels as D, C, F, E, B, A.
    assert train["sensor"].tolist() == ["F", "C", "D", "C", "F", "F"]
    assert validation["sensor"].tolist() == ["E"]
    assert test["sensor"].tolist() == ["A", "B", "A"]
    assert train.index.tolist() == [8, 3, 4, 4, 0, 0]
    assert sorted(pd.concat([train, validation, test])["reading"].tolist()) == list(range(10))
    assert train.dtypes.equals(frame.dtypes)


def test_reordering_rows_preserves_group_assignment() -> None:
    frame = observations()
    first = exercise_call(split_sensor_groups, frame, "sensor", 0.5, 0.2, 13)
    second = exercise_call(split_sensor_groups, frame.iloc[::-1], "sensor", 0.5, 0.2, 13)
    for left, right in zip(first, second, strict=True):
        assert set(left["sensor"]) == set(right["sensor"])
    groups = [set(part["sensor"]) for part in first]
    assert not groups[0] & groups[1]
    assert not groups[0] & groups[2]
    assert not groups[1] & groups[2]


def test_repeatable_without_consuming_global_randomness() -> None:
    state_before = np.random.get_state()
    first = exercise_call(split_sensor_groups, observations(), "sensor", 0.5, 0.2, 7)
    second = exercise_call(split_sensor_groups, observations(), "sensor", 0.5, 0.2, 7)
    state_after = np.random.get_state()
    for left, right in zip(first, second, strict=True):
        pd.testing.assert_frame_equal(left, right)
    assert state_before[0] == state_after[0]
    np.testing.assert_array_equal(state_before[1], state_after[1])
    assert state_before[2:] == state_after[2:]


@pytest.mark.parametrize("partition", [0, 1, 2])
def test_outputs_are_independent_copies(partition: int) -> None:
    frame = observations()
    original = frame.copy(deep=True)
    parts = exercise_call(split_sensor_groups, frame, "sensor", 0.5, 0.2)
    backups = [part.copy(deep=True) for part in parts]
    parts[partition].iloc[0, 1] = -100
    pd.testing.assert_frame_equal(frame, original)
    for index, backup in enumerate(backups):
        if index != partition:
            pd.testing.assert_frame_equal(parts[index], backup)


@pytest.mark.parametrize(
    ("train_fraction", "validation_fraction"),
    [
        (0.0, 0.2),
        (0.5, 0.0),
        (-0.2, 0.2),
        (0.8, 0.2),
        (0.9, 0.4),
        (np.nan, 0.2),
        (0.5, np.inf),
        (0.1, 0.2),
    ],
)
def test_invalid_or_empty_partitions_are_rejected(
    train_fraction: float, validation_fraction: float
) -> None:
    with pytest.raises(ValueError, match=r"fraction|group|partition"):
        exercise_call(
            split_sensor_groups, observations(), "sensor", train_fraction, validation_fraction
        )


@pytest.mark.parametrize("bad_group", [None, "", "   ", 7, np.nan])
def test_invalid_sensor_labels_are_rejected(bad_group: str | int | float | None) -> None:
    frame = observations().astype({"sensor": object})
    frame.iloc[0, 0] = bad_group
    with pytest.raises(ValueError, match=r"group|sensor"):
        exercise_call(split_sensor_groups, frame, "sensor", 0.5, 0.2)


def test_missing_or_ambiguous_group_column_and_empty_frame_are_rejected() -> None:
    for frame in [
        pd.DataFrame(),
        observations().rename(columns={"sensor": "site"}),
        pd.DataFrame([["A", "B"]], columns=["sensor", "sensor"]),
    ]:
        with pytest.raises(ValueError, match=r"frame|column|group|empty"):
            exercise_call(split_sensor_groups, frame, "sensor", 0.5, 0.2)


def test_negative_seed_is_rejected() -> None:
    with pytest.raises(ValueError, match="seed"):
        exercise_call(split_sensor_groups, observations(), "sensor", 0.5, 0.2, -1)
