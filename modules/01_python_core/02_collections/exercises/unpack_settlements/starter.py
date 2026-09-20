"""Student boundary for validating and unpacking settlement records."""

from collections.abc import Sequence
from decimal import Decimal, InvalidOperation


def parse_settlement(row: Sequence[str]) -> tuple[str, Decimal, str]:
    """Parse a transaction ID, decimal amount, and currency from one row."""
    if len(row) != 3:
        raise ValueError("settlement row must contain exactly three fields")

    transaction_id, amount_text, currency = row
    if not isinstance(transaction_id, str) or not transaction_id.strip():
        raise ValueError("transaction ID must be a nonblank string")
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("currency must be a nonblank string")

    try:
        Decimal(amount_text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("amount must be valid decimal text") from exc

    raise NotImplementedError("unpack the settlement row")
