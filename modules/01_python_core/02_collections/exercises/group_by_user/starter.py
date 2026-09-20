"""Student boundary for grouping transaction amounts by user."""

from collections.abc import Iterable
from decimal import Decimal


def group_amounts_by_user(
    transactions: Iterable[tuple[str, Decimal]],
) -> dict[str, list[Decimal]]:
    """Group transaction amounts by user while preserving input order."""
    transaction_rows = list(transactions)
    for user_id, amount in transaction_rows:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user ID must be a nonblank string")
        if not isinstance(amount, Decimal):
            raise ValueError("amount must be a Decimal")

    raise NotImplementedError("group transaction amounts by user")
