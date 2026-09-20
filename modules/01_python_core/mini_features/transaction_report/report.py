"""Typed starter boundary for the transaction-report mini-feature."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import NotRequired, TypedDict


class TransactionRow(TypedDict):
    """One validated transaction accepted by the report."""

    id: str
    amount: Decimal
    currency: str
    status: str
    merchant: str
    metadata: NotRequired[dict[str, str]]


@dataclass(frozen=True)
class CurrencyTotal:
    """A currency and its exact aggregate amount."""

    currency: str
    total: Decimal


@dataclass(frozen=True)
class StatusCount:
    """A transaction status and its occurrence count."""

    status: str
    count: int


@dataclass(frozen=True)
class MerchantTotal:
    """A merchant and its exact aggregate amount."""

    merchant: str
    total: Decimal


@dataclass(frozen=True)
class TransactionReport:
    """Immutable aggregate output produced from transaction rows."""

    transaction_count: int
    total_amount: Decimal
    totals_by_currency: tuple[CurrencyTotal, ...]
    counts_by_status: tuple[StatusCount, ...]
    top_merchants: tuple[MerchantTotal, ...]


def build_transaction_report(rows: Iterable[TransactionRow]) -> TransactionReport:
    """Aggregate one traversal of validated rows into a deterministic report.

    Raise:
        ValueError: If a row violates the schema documented in the exercise.
    """
    raise NotImplementedError("build the transaction analytics report")
