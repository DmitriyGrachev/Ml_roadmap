"""Acceptance tests for the transaction-report mini-feature."""

from collections.abc import Iterator
from copy import deepcopy
from dataclasses import FrozenInstanceError
from decimal import Decimal
from typing import cast

import pytest

from roadmap_tools import exercise_call

from .report import (
    CurrencyTotal,
    MerchantTotal,
    StatusCount,
    TransactionReport,
    TransactionRow,
    build_transaction_report,
)


def transaction(
    transaction_id: str,
    amount: str,
    currency: str,
    status: str,
    merchant: str,
    *,
    metadata: dict[str, str] | None = None,
) -> TransactionRow:
    row: TransactionRow = {
        "id": transaction_id,
        "amount": Decimal(amount),
        "currency": currency,
        "status": status,
        "merchant": merchant,
    }
    if metadata is not None:
        row["metadata"] = metadata
    return row


class OneShotRows:
    """Raise if a report implementation asks for a second traversal."""

    def __init__(self, rows: list[TransactionRow]) -> None:
        self._rows = iter(rows)
        self.iterations = 0

    def __iter__(self) -> Iterator[TransactionRow]:
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("transaction rows were traversed more than once")
        return self._rows


def test_transaction_report_is_frozen() -> None:
    report = TransactionReport(
        transaction_count=0,
        total_amount=Decimal("0"),
        totals_by_currency=(),
        counts_by_status=(),
        top_merchants=(),
    )

    with pytest.raises(FrozenInstanceError):
        exercise_call(setattr, report, "transaction_count", 1)


@pytest.mark.parametrize(
    ("record", "field", "replacement"),
    [
        pytest.param(
            CurrencyTotal(currency="EUR", total=Decimal("1.00")),
            "total",
            Decimal("2.00"),
            id="currency-total",
        ),
        pytest.param(
            StatusCount(status="posted", count=1),
            "count",
            2,
            id="status-count",
        ),
        pytest.param(
            MerchantTotal(merchant="Alpha", total=Decimal("1.00")),
            "merchant",
            "Beta",
            id="merchant-total",
        ),
    ],
)
def test_report_aggregate_value_objects_are_frozen(
    record: object,
    field: str,
    replacement: object,
) -> None:
    with pytest.raises(FrozenInstanceError):
        exercise_call(setattr, record, field, replacement)


@pytest.mark.student_exercise
def test_report_contains_every_aggregate_in_deterministic_order() -> None:
    rows = OneShotRows(
        [
            transaction("txn-1", "3.00", "USD", "reversed", "Zen Market"),
            transaction("txn-2", "5.00", "EUR", "posted", "Alpha Shop"),
            transaction("txn-3", "5.00", "USD", "reversed", "Beta Store"),
            transaction("txn-4", "1.00", "EUR", "pending", "Alpha Shop"),
        ]
    )

    report = exercise_call(build_transaction_report, rows)

    assert report == TransactionReport(
        transaction_count=4,
        total_amount=Decimal("14.00"),
        totals_by_currency=(
            CurrencyTotal(currency="EUR", total=Decimal("6.00")),
            CurrencyTotal(currency="USD", total=Decimal("8.00")),
        ),
        counts_by_status=(
            StatusCount(status="pending", count=1),
            StatusCount(status="posted", count=1),
            StatusCount(status="reversed", count=2),
        ),
        top_merchants=(
            MerchantTotal(merchant="Alpha Shop", total=Decimal("6.00")),
            MerchantTotal(merchant="Beta Store", total=Decimal("5.00")),
            MerchantTotal(merchant="Zen Market", total=Decimal("3.00")),
        ),
    )
    assert rows.iterations == 1


@pytest.mark.student_exercise
def test_report_limits_merchants_to_three_and_breaks_total_ties_alphabetically() -> None:
    rows = (
        transaction(transaction_id, amount, "EUR", "posted", merchant)
        for transaction_id, amount, merchant in (
            ("txn-1", "5.00", "Beta"),
            ("txn-2", "5.00", "Alpha"),
            ("txn-3", "2.00", "Delta"),
            ("txn-4", "2.00", "Charlie"),
        )
    )

    report = exercise_call(build_transaction_report, rows)

    assert report.top_merchants == (
        MerchantTotal(merchant="Alpha", total=Decimal("5.00")),
        MerchantTotal(merchant="Beta", total=Decimal("5.00")),
        MerchantTotal(merchant="Charlie", total=Decimal("2.00")),
    )


@pytest.mark.student_exercise
def test_empty_report_uses_neutral_values() -> None:
    assert exercise_call(build_transaction_report, iter(())) == TransactionReport(
        transaction_count=0,
        total_amount=Decimal("0"),
        totals_by_currency=(),
        counts_by_status=(),
        top_merchants=(),
    )


@pytest.mark.student_exercise
def test_report_preserves_decimal_arithmetic_exactly() -> None:
    rows = (transaction("txn-1", amount, "EUR", "posted", "Alpha") for amount in ("0.1", "0.2"))

    report = exercise_call(build_transaction_report, rows)

    assert report.total_amount == Decimal("0.3")
    assert report.totals_by_currency[0].total == Decimal("0.3")
    assert report.top_merchants[0].total == Decimal("0.3")
    assert isinstance(report.total_amount, Decimal)


@pytest.mark.student_exercise
def test_report_does_not_mutate_rows_or_nested_metadata() -> None:
    rows = [
        transaction(
            "txn-2",
            "4.00",
            "USD",
            "posted",
            "Beta",
            metadata={"risk": "low"},
        ),
        transaction(
            "txn-1",
            "6.00",
            "USD",
            "posted",
            "Alpha",
            metadata={"risk": "high"},
        ),
    ]
    snapshot = deepcopy(rows)

    exercise_call(build_transaction_report, rows)

    assert rows == snapshot


@pytest.mark.student_exercise
@pytest.mark.parametrize(
    "invalid_row",
    [
        pytest.param(
            {
                "amount": Decimal("1.00"),
                "currency": "EUR",
                "status": "posted",
                "merchant": "Alpha",
            },
            id="missing-id",
        ),
        pytest.param(
            {
                "id": "txn-1",
                "currency": "EUR",
                "status": "posted",
                "merchant": "Alpha",
            },
            id="missing-amount",
        ),
        pytest.param(
            {
                "id": "txn-1",
                "amount": Decimal("1.00"),
                "status": "posted",
                "merchant": "Alpha",
            },
            id="missing-currency",
        ),
        pytest.param(
            {
                "id": "txn-1",
                "amount": Decimal("1.00"),
                "currency": "EUR",
                "merchant": "Alpha",
            },
            id="missing-status",
        ),
        pytest.param(
            {
                "id": "txn-1",
                "amount": Decimal("1.00"),
                "currency": "EUR",
                "status": "posted",
            },
            id="missing-merchant",
        ),
        pytest.param(
            {
                "id": "txn-1",
                "amount": 4.5,
                "currency": "EUR",
                "status": "posted",
                "merchant": "Alpha",
            },
            id="non-decimal-amount",
        ),
        *[
            pytest.param(
                {
                    "id": "txn-1",
                    "amount": amount,
                    "currency": "EUR",
                    "status": "posted",
                    "merchant": "Alpha",
                },
                id=case_id,
            )
            for amount, case_id in (
                (Decimal("NaN"), "nan-amount"),
                (Decimal("Infinity"), "positive-infinity-amount"),
                (Decimal("-Infinity"), "negative-infinity-amount"),
                (Decimal("-0.01"), "negative-amount"),
            )
        ],
        *[
            pytest.param(
                {
                    "id": identifier,
                    "amount": Decimal("1.00"),
                    "currency": "EUR",
                    "status": "posted",
                    "merchant": "Alpha",
                },
                id=case_id,
            )
            for identifier, case_id in ((" ", "blank-id"), (42, "non-string-id"))
        ],
        *[
            pytest.param(
                {
                    "id": "txn-1",
                    "amount": Decimal("1.00"),
                    "currency": currency,
                    "status": "posted",
                    "merchant": "Alpha",
                },
                id=case_id,
            )
            for currency, case_id in (
                ("eur", "lowercase-currency"),
                ("E1R", "non-letter-currency"),
                ("ÉUR", "non-ascii-currency"),
                (" EU", "whitespace-currency"),
                (978, "non-string-currency"),
            )
        ],
        *[
            pytest.param(
                {
                    "id": "txn-1",
                    "amount": Decimal("1.00"),
                    "currency": "EUR",
                    "status": status,
                    "merchant": "Alpha",
                },
                id=case_id,
            )
            for status, case_id in ((" ", "blank-status"), (1, "non-string-status"))
        ],
        *[
            pytest.param(
                {
                    "id": "txn-1",
                    "amount": Decimal("1.00"),
                    "currency": "EUR",
                    "status": "posted",
                    "merchant": merchant,
                },
                id=case_id,
            )
            for merchant, case_id in ((" ", "blank-merchant"), (1, "non-string-merchant"))
        ],
        pytest.param(
            {
                "id": "txn-1",
                "amount": Decimal("1.00"),
                "currency": "EUR",
                "status": "posted",
                "merchant": "Alpha",
                "unexpected": "field",
            },
            id="unexpected-field",
        ),
        *[
            pytest.param(
                {
                    "id": "txn-1",
                    "amount": Decimal("1.00"),
                    "currency": "EUR",
                    "status": "posted",
                    "merchant": "Alpha",
                    "metadata": metadata,
                },
                id=case_id,
            )
            for metadata, case_id in (
                (None, "none-metadata"),
                ("risk=high", "non-dict-metadata"),
                ({1: "high"}, "non-string-metadata-key"),
                ({"risk": 4}, "non-string-metadata-value"),
            )
        ],
    ],
)
def test_report_rejects_a_malformed_row(invalid_row: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="transaction row"):
        exercise_call(build_transaction_report, [cast(TransactionRow, invalid_row)])
