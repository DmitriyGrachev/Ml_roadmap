"""Tests for the group-by-user student exercise."""

from decimal import Decimal
from typing import cast

import pytest

from roadmap_tools import exercise_call

from .starter import group_amounts_by_user


@pytest.mark.student_exercise
def test_group_amounts_by_user_preserves_input_order_within_each_user() -> None:
    transactions = [
        ("user-b", Decimal("3.00")),
        ("user-a", Decimal("1.25")),
        ("user-b", Decimal("2.50")),
    ]

    assert list(exercise_call(group_amounts_by_user, transactions).items()) == [
        ("user-b", [Decimal("3.00"), Decimal("2.50")]),
        ("user-a", [Decimal("1.25")]),
    ]


@pytest.mark.student_exercise
def test_group_amounts_by_user_retains_decimal_values() -> None:
    amount = Decimal("0.10")

    result = exercise_call(group_amounts_by_user, [("user-a", amount)])

    assert result == {"user-a": [amount]}
    assert isinstance(result["user-a"][0], Decimal)


@pytest.mark.student_exercise
def test_group_amounts_by_user_accepts_a_one_shot_generator() -> None:
    transactions = (
        transaction for transaction in (("user-a", Decimal("4.00")), ("user-a", Decimal("5.00")))
    )

    assert exercise_call(group_amounts_by_user, transactions) == {
        "user-a": [Decimal("4.00"), Decimal("5.00")]
    }


@pytest.mark.student_exercise
def test_group_amounts_by_user_returns_empty_mapping_for_empty_input() -> None:
    assert exercise_call(group_amounts_by_user, []) == {}


@pytest.mark.parametrize("user_id", ["", "   ", 42])
def test_group_amounts_by_user_rejects_invalid_user_ids(user_id: object) -> None:
    transactions = cast(list[tuple[str, Decimal]], [(user_id, Decimal("1.00"))])

    with pytest.raises(ValueError, match="user ID"):
        exercise_call(group_amounts_by_user, transactions)


def test_group_amounts_by_user_rejects_non_decimal_amounts() -> None:
    transactions = cast(list[tuple[str, Decimal]], [("user-a", "1.00")])

    with pytest.raises(ValueError, match="amount"):
        exercise_call(group_amounts_by_user, transactions)
