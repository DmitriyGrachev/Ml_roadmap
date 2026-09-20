"""Stage 2 report contracts and unfinished analytics boundaries."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from banking_ai_lab.domain import Currency, Transaction, TransactionStatus


@dataclass(frozen=True, slots=True)
class CurrencySummary:
    """Count and exact amount total for one currency."""

    currency: Currency
    transaction_count: int
    total_amount: Decimal


@dataclass(frozen=True, slots=True)
class StatusSummary:
    """Count for one transaction status."""

    status: TransactionStatus
    transaction_count: int


@dataclass(frozen=True, slots=True)
class MerchantSummary:
    """Count and exact amount total for one merchant."""

    merchant: str
    transaction_count: int
    total_amount: Decimal


@dataclass(frozen=True, slots=True)
class TransactionReport:
    """Deterministic immutable summary of a transaction collection."""

    transaction_count: int
    fraud_count: int
    period_start: datetime | None
    period_end: datetime | None
    currencies: tuple[CurrencySummary, ...]
    statuses: tuple[StatusSummary, ...]
    top_merchants: tuple[MerchantSummary, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "currencies", tuple(self.currencies))
        object.__setattr__(self, "statuses", tuple(self.statuses))
        object.__setattr__(self, "top_merchants", tuple(self.top_merchants))
        if len(self.top_merchants) > 3:
            raise ValueError("a transaction report contains at most three merchants")


def build_report(transactions: Iterable[Transaction]) -> TransactionReport:
    """Build a deterministic report from one pass over *transactions*."""
    raise NotImplementedError("build the transaction report")


def write_report_json(report: TransactionReport, path: Path) -> None:
    """Write *report* as deterministic UTF-8 JSON through atomic replacement."""
    if not path.parent.is_dir():
        raise FileNotFoundError(path.parent)
    raise NotImplementedError("write the transaction report as atomic JSON")
