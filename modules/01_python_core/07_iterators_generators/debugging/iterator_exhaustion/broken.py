"""Intentionally broken one-shot iterator example."""

from collections.abc import Iterable
from decimal import Decimal


def summarize_amounts(amounts: Iterable[Decimal]) -> tuple[int, Decimal]:
    """Return the item count and total, but accidentally consume one-shot inputs twice."""
    count = sum(1 for _ in amounts)
    total = sum(amounts, start=Decimal("0"))
    return count, total
