"""Student boundary for replaying a reservation ledger without overspending."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class BudgetEvent:
    request_id: str
    kind: Literal["reserve", "settle", "cancel"]
    amount: Decimal


@dataclass(frozen=True)
class Reservation:
    request_id: str
    reserved: Decimal
    status: Literal["pending", "settled", "cancelled"]
    actual: Decimal | None


@dataclass(frozen=True)
class BudgetReport:
    limit: Decimal
    spent: Decimal
    held: Decimal
    available: Decimal
    reservations: tuple[Reservation, ...]


def summarize_budget(limit: Decimal, events: Sequence[BudgetEvent]) -> BudgetReport:
    """Replay the README's reserve/settle/cancel protocol as one local computation."""
    # TODO: validate and replay events with idempotency and budget invariants.
    raise NotImplementedError("summarize request budget reservations")
