"""Tests for the slice-windows student exercise."""

from typing import cast

import pytest

from roadmap_tools import exercise_call

from .starter import transaction_windows


@pytest.mark.student_exercise
def test_transaction_windows_includes_full_and_final_partial_windows() -> None:
    assert exercise_call(transaction_windows, ["txn-1", "txn-2", "txn-3"], 2) == [
        ("txn-1", "txn-2"),
        ("txn-3",),
    ]


@pytest.mark.student_exercise
def test_transaction_windows_supports_a_size_larger_than_the_input() -> None:
    assert exercise_call(transaction_windows, ["txn-1", "txn-2"], 5) == [
        ("txn-1", "txn-2"),
    ]


@pytest.mark.student_exercise
def test_transaction_windows_supports_size_one() -> None:
    assert exercise_call(transaction_windows, ["txn-1", "txn-2"], 1) == [
        ("txn-1",),
        ("txn-2",),
    ]


@pytest.mark.student_exercise
def test_transaction_windows_returns_empty_list_for_empty_input() -> None:
    assert exercise_call(transaction_windows, [], 3) == []


@pytest.mark.parametrize("size", [0, -1])
def test_transaction_windows_rejects_non_positive_sizes(size: int) -> None:
    with pytest.raises(ValueError, match="size must be positive"):
        exercise_call(transaction_windows, ["txn-1"], size)


@pytest.mark.parametrize("transaction_id", ["", " ", 42])
def test_transaction_windows_rejects_invalid_transaction_ids(transaction_id: object) -> None:
    transaction_ids = cast(list[str], ["txn-1", transaction_id])

    with pytest.raises(ValueError, match="transaction ID"):
        exercise_call(transaction_windows, transaction_ids, 1)
