"""Characterization tests for the Java-shaped grouping review fixture."""

from copy import deepcopy
from decimal import Decimal

from .review_me import TransactionRow, group_transactions


def test_groups_full_rows_in_first_seen_user_order() -> None:
    rows: list[TransactionRow] = [
        {
            "id": "txn-001",
            "user_id": "user-b",
            "amount": Decimal("12.40"),
            "currency": "USD",
            "status": "posted",
        },
        {
            "id": "txn-002",
            "user_id": "user-a",
            "amount": Decimal("8.10"),
            "currency": "EUR",
            "status": "pending",
        },
        {
            "id": "txn-003",
            "user_id": "user-b",
            "amount": Decimal("0.50"),
            "currency": "USD",
            "status": "reversed",
        },
    ]

    grouped = group_transactions(rows)

    assert list(grouped) == ["user-b", "user-a"]
    assert grouped == {
        "user-b": [
            {
                "id": "txn-001",
                "user_id": "user-b",
                "amount": Decimal("12.40"),
                "currency": "USD",
                "status": "posted",
            },
            {
                "id": "txn-003",
                "user_id": "user-b",
                "amount": Decimal("0.50"),
                "currency": "USD",
                "status": "reversed",
            },
        ],
        "user-a": [
            {
                "id": "txn-002",
                "user_id": "user-a",
                "amount": Decimal("8.10"),
                "currency": "EUR",
                "status": "pending",
            }
        ],
    }


def test_grouping_does_not_mutate_nested_input_rows() -> None:
    rows: list[TransactionRow] = [
        {
            "id": "txn-004",
            "user_id": "user-a",
            "amount": Decimal("3.75"),
            "currency": "GBP",
            "status": "posted",
        }
    ]
    original_rows = deepcopy(rows)

    group_transactions(rows)

    assert rows == original_rows


def test_empty_input_produces_no_groups() -> None:
    assert group_transactions([]) == {}
