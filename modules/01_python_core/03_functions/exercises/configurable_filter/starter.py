"""Student boundary for building configurable transaction predicates."""

from collections.abc import Callable
from decimal import Decimal
from typing import TypedDict


class TransactionRow(TypedDict):
    """Transaction fields accepted by the filter predicate."""

    id: str
    user_id: str
    amount: Decimal
    currency: str
    status: str


type TransactionPredicate = Callable[[TransactionRow], bool]


def make_transaction_filter(
    *,
    minimum: Decimal = Decimal("0"),
    currencies: frozenset[str] | None = None,
    predicate: TransactionPredicate | None = None,
) -> TransactionPredicate:
    """Build a predicate from an amount, currencies, and an optional predicate.

    Raise:
        ValueError: If ``minimum`` is negative.
    """
    if minimum < Decimal("0"):
        raise ValueError("minimum must not be negative")

    raise NotImplementedError("build a configurable transaction filter")
