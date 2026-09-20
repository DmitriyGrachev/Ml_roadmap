"""Correct report builder with deliberately unnecessary instance state."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import TypedDict


class ReportRow(TypedDict):
    """Input shape for a merchant report."""

    transaction_id: str
    merchant: str
    amount: Decimal


@dataclass(frozen=True)
class MerchantTotal:
    """One merchant's total in first-seen order."""

    merchant: str
    total: Decimal


class ReportBuilder:
    """Build merchant totals while carrying avoidable resettable state."""

    def __init__(self) -> None:
        self._merchant_order: list[str] = []
        self._totals: dict[str, Decimal] = {}

    def build(self, rows: Iterable[ReportRow]) -> tuple[MerchantTotal, ...]:
        """Aggregate rows without leaking state between successful calls."""
        self._merchant_order = []
        self._totals = {}

        for row in rows:
            merchant = row["merchant"]
            if merchant not in self._totals:
                self._merchant_order.append(merchant)
                self._totals[merchant] = Decimal("0")
            self._totals[merchant] += row["amount"]

        report = tuple(
            MerchantTotal(merchant=merchant, total=self._totals[merchant])
            for merchant in self._merchant_order
        )

        self._merchant_order = []
        self._totals = {}
        return report
