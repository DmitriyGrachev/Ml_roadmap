"""Tests for the detect-duplicates student exercise."""

import pytest

from roadmap_tools import exercise_call

from .starter import find_duplicate_ids


@pytest.mark.student_exercise
def test_find_duplicate_ids_returns_every_repeated_id() -> None:
    transactions = (
        row
        for row in (
            {"id": "txn-002"},
            {"id": "txn-001"},
            {"id": "txn-002"},
            {"id": "txn-003"},
            {"id": "txn-001"},
        )
    )

    assert exercise_call(find_duplicate_ids, transactions) == {"txn-001", "txn-002"}


@pytest.mark.student_exercise
def test_find_duplicate_ids_returns_empty_set_for_unique_ids() -> None:
    transactions = [{"id": "txn-001"}, {"id": "txn-002"}]

    assert exercise_call(find_duplicate_ids, transactions) == set()


@pytest.mark.student_exercise
def test_find_duplicate_ids_accepts_an_empty_generator() -> None:
    empty_rows: tuple[dict[str, object], ...] = ()
    transactions = (row for row in empty_rows)

    assert exercise_call(find_duplicate_ids, transactions) == set()


@pytest.mark.parametrize("invalid_id", [None, 42, "", "   "])
def test_find_duplicate_ids_rejects_missing_or_invalid_ids(invalid_id: object) -> None:
    transaction: dict[str, object] = {} if invalid_id is None else {"id": invalid_id}

    with pytest.raises(ValueError, match="transaction ID"):
        exercise_call(find_duplicate_ids, [transaction])
