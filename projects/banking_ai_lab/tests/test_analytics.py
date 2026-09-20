"""Stage 2 report and atomic JSON acceptance contracts."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, NoReturn, cast
from uuid import UUID

import pytest
from banking_ai_lab.analytics import (
    CurrencySummary,
    MerchantSummary,
    StatusSummary,
    TransactionReport,
    build_report,
    write_report_json,
)
from banking_ai_lab.domain import Transaction

from roadmap_tools import exercise_call


def make_transaction(
    index: int,
    *,
    amount: str,
    currency: str,
    merchant: str,
    status: str,
    timestamp: datetime,
    is_fraud: bool = False,
) -> Transaction:
    return Transaction.model_validate(
        {
            "id": UUID(int=index),
            "user_id": f"user-{index:04d}",
            "amount": Decimal(amount),
            "currency": currency,
            "merchant": merchant,
            "category": "groceries",
            "timestamp": timestamp,
            "status": status,
            "is_fraud": is_fraud,
        }
    )


def report_transactions() -> list[Transaction]:
    return [
        make_transaction(
            6,
            amount="15.15",
            currency="USD",
            merchant="Epsilon",
            status="approved",
            timestamp=datetime(2025, 1, 6, tzinfo=UTC),
        ),
        make_transaction(
            2,
            amount="20.00",
            currency="EUR",
            merchant="Beta",
            status="approved",
            timestamp=datetime(2025, 1, 1, tzinfo=UTC),
            is_fraud=True,
        ),
        make_transaction(
            4,
            amount="20.20",
            currency="USD",
            merchant="Alpha",
            status="declined",
            timestamp=datetime(2025, 1, 3, tzinfo=UTC),
        ),
        make_transaction(
            1,
            amount="10.00",
            currency="EUR",
            merchant="Beta",
            status="approved",
            timestamp=datetime(2025, 1, 2, tzinfo=UTC),
        ),
        make_transaction(
            5,
            amount="5.05",
            currency="USD",
            merchant="Delta",
            status="pending",
            timestamp=datetime(2025, 1, 4, tzinfo=UTC),
        ),
        make_transaction(
            3,
            amount="30.00",
            currency="GBP",
            merchant="Gamma",
            status="refunded",
            timestamp=datetime(2025, 1, 5, tzinfo=UTC),
            is_fraud=True,
        ),
    ]


def sample_report() -> TransactionReport:
    return TransactionReport(
        transaction_count=3,
        fraud_count=1,
        period_start=datetime(2025, 1, 1, 8, tzinfo=UTC),
        period_end=datetime(2025, 1, 2, 9, tzinfo=UTC),
        currencies=(CurrencySummary("EUR", 2, Decimal("30.30")),),
        statuses=(StatusSummary("approved", 3),),
        top_merchants=(MerchantSummary("Café Aurora", 2, Decimal("30.30")),),
    )


class OneShotTransactions(Iterable[Transaction]):
    def __init__(self, transactions: list[Transaction]) -> None:
        self._transactions = transactions
        self._iterations = 0

    def __iter__(self) -> Iterator[Transaction]:
        self._iterations += 1
        if self._iterations > 1:
            raise AssertionError("transaction iterable was consumed more than once")
        return iter(self._transactions)


@pytest.mark.parametrize(
    "record",
    [
        CurrencySummary("EUR", 1, Decimal("1.00")),
        StatusSummary("approved", 1),
        MerchantSummary("Aurora", 1, Decimal("1.00")),
    ],
)
def test_summary_records_are_frozen(record: object) -> None:
    with pytest.raises(FrozenInstanceError):
        cast(Any, record).transaction_count = 99


def test_transaction_report_is_frozen_and_copies_summary_collections() -> None:
    currencies = [CurrencySummary("EUR", 1, Decimal("1.00"))]
    statuses = [StatusSummary("approved", 1)]
    merchants = [MerchantSummary("Aurora", 1, Decimal("1.00"))]
    report = TransactionReport(
        transaction_count=1,
        fraud_count=0,
        period_start=datetime(2025, 1, 1, tzinfo=UTC),
        period_end=datetime(2025, 1, 1, tzinfo=UTC),
        currencies=currencies,  # type: ignore[arg-type]
        statuses=statuses,  # type: ignore[arg-type]
        top_merchants=merchants,  # type: ignore[arg-type]
    )
    currencies.clear()
    statuses.clear()
    merchants.clear()

    assert report.currencies == (CurrencySummary("EUR", 1, Decimal("1.00")),)
    assert report.statuses == (StatusSummary("approved", 1),)
    assert report.top_merchants == (MerchantSummary("Aurora", 1, Decimal("1.00")),)
    with pytest.raises(FrozenInstanceError):
        cast(Any, report).transaction_count = 2


def test_transaction_report_rejects_more_than_three_merchants() -> None:
    merchants = tuple(
        MerchantSummary(f"Merchant {index}", 1, Decimal("1.00")) for index in range(4)
    )

    with pytest.raises(ValueError, match="at most three merchants"):
        TransactionReport(
            transaction_count=4,
            fraud_count=0,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 1, 1, tzinfo=UTC),
            currencies=(),
            statuses=(),
            top_merchants=merchants,
        )


@pytest.mark.student_exercise
def test_build_report_counts_transactions_and_fraud_independently() -> None:
    report = exercise_call(build_report, report_transactions())

    assert report.transaction_count == 6
    assert report.fraud_count == 2


@pytest.mark.student_exercise
def test_build_report_uses_the_minimum_and_maximum_utc_timestamp() -> None:
    report = exercise_call(build_report, report_transactions())

    assert report.period_start == datetime(2025, 1, 1, tzinfo=UTC)
    assert report.period_end == datetime(2025, 1, 6, tzinfo=UTC)
    assert report.period_start is not None
    assert report.period_start.tzinfo is UTC
    assert report.period_end is not None
    assert report.period_end.tzinfo is UTC


@pytest.mark.student_exercise
def test_build_report_orders_currency_counts_and_exact_totals_alphabetically() -> None:
    report = exercise_call(build_report, report_transactions())

    assert report.currencies == (
        CurrencySummary("EUR", 2, Decimal("30.00")),
        CurrencySummary("GBP", 1, Decimal("30.00")),
        CurrencySummary("USD", 3, Decimal("40.40")),
    )


@pytest.mark.student_exercise
def test_build_report_preserves_decimal_arithmetic_exactly() -> None:
    transactions = [
        make_transaction(
            1,
            amount="0.10",
            currency="USD",
            merchant="Aurora",
            status="approved",
            timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        ),
        make_transaction(
            2,
            amount="0.20",
            currency="USD",
            merchant="Aurora",
            status="approved",
            timestamp=datetime(2025, 1, 2, tzinfo=UTC),
        ),
    ]

    report = exercise_call(build_report, transactions)

    assert report.currencies[0].total_amount == Decimal("0.30")
    assert report.top_merchants[0].total_amount == Decimal("0.30")


@pytest.mark.student_exercise
def test_build_report_orders_status_counts_alphabetically() -> None:
    report = exercise_call(build_report, report_transactions())

    assert report.statuses == (
        StatusSummary("approved", 3),
        StatusSummary("declined", 1),
        StatusSummary("pending", 1),
        StatusSummary("refunded", 1),
    )


@pytest.mark.student_exercise
def test_build_report_limits_merchants_and_breaks_total_ties_by_name() -> None:
    report = exercise_call(build_report, report_transactions())

    assert report.top_merchants == (
        MerchantSummary("Beta", 2, Decimal("30.00")),
        MerchantSummary("Gamma", 1, Decimal("30.00")),
        MerchantSummary("Alpha", 1, Decimal("20.20")),
    )


@pytest.mark.student_exercise
def test_build_report_returns_a_neutral_empty_report() -> None:
    report = exercise_call(build_report, iter(()))

    assert report == TransactionReport(
        transaction_count=0,
        fraud_count=0,
        period_start=None,
        period_end=None,
        currencies=(),
        statuses=(),
        top_merchants=(),
    )


@pytest.mark.student_exercise
def test_build_report_consumes_a_one_shot_iterable_once() -> None:
    report = exercise_call(build_report, OneShotTransactions(report_transactions()))

    assert report.transaction_count == 6


@pytest.mark.student_exercise
def test_build_report_does_not_reorder_or_replace_caller_items() -> None:
    transactions = report_transactions()
    original_order = tuple(transactions)
    original_ids = tuple(id(item) for item in transactions)

    exercise_call(build_report, transactions)

    assert tuple(transactions) == original_order
    assert tuple(id(item) for item in transactions) == original_ids


@pytest.mark.student_exercise
def test_write_report_json_emits_deterministic_utf8_domain_values(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    report = sample_report()

    exercise_call(write_report_json, report, first)
    exercise_call(write_report_json, report, second)

    expected = {
        "transaction_count": 3,
        "fraud_count": 1,
        "period_start": "2025-01-01T08:00:00+00:00",
        "period_end": "2025-01-02T09:00:00+00:00",
        "currencies": [{"currency": "EUR", "transaction_count": 2, "total_amount": "30.30"}],
        "statuses": [{"status": "approved", "transaction_count": 3}],
        "top_merchants": [
            {"merchant": "Café Aurora", "transaction_count": 2, "total_amount": "30.30"}
        ],
    }
    text = first.read_text(encoding="utf-8")
    assert json.loads(text) == expected
    assert "Café Aurora" in text
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.student_exercise
def test_write_report_json_replaces_through_a_sibling_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "report.json"
    replacements: list[tuple[Path, Path]] = []
    original_replace = os.replace

    def recording_replace(source: os.PathLike[str] | str, target: os.PathLike[str] | str) -> None:
        replacements.append((Path(source), Path(target)))
        original_replace(source, target)

    monkeypatch.setattr(os, "replace", recording_replace)

    exercise_call(write_report_json, sample_report(), destination)

    assert len(replacements) == 1
    temporary, replaced_destination = replacements[0]
    assert temporary.parent == destination.parent
    assert temporary != destination
    assert replaced_destination == destination
    assert destination.is_file()
    assert not temporary.exists()


@pytest.mark.student_exercise
def test_write_report_json_refuses_a_missing_parent(tmp_path: Path) -> None:
    destination = tmp_path / "missing" / "report.json"

    with pytest.raises(FileNotFoundError):
        exercise_call(write_report_json, sample_report(), destination)

    assert not destination.parent.exists()


@pytest.mark.student_exercise
def test_serialization_failure_preserves_target_cleans_temp_and_propagates_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "report.json"
    neighbor = tmp_path / "keep.tmp"
    destination.write_bytes(b"original-report")
    neighbor.write_bytes(b"unrelated")
    error = UnicodeError("serialization failed")

    def fail_serialization(*_args: object, **_kwargs: object) -> NoReturn:
        raise error

    monkeypatch.setattr(json, "dump", fail_serialization)
    monkeypatch.setattr(json, "dumps", fail_serialization)

    with pytest.raises(UnicodeError) as caught:
        exercise_call(write_report_json, sample_report(), destination)

    assert caught.value is error
    assert destination.read_bytes() == b"original-report"
    assert neighbor.read_bytes() == b"unrelated"
    assert {path.name for path in tmp_path.iterdir()} == {"report.json", "keep.tmp"}


@pytest.mark.student_exercise
def test_replacement_failure_preserves_target_cleans_temp_and_propagates_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "report.json"
    neighbor = tmp_path / "keep.tmp"
    destination.write_bytes(b"original-report")
    neighbor.write_bytes(b"unrelated")
    error = OSError("replacement failed")

    def fail_replace(_source: os.PathLike[str] | str, _target: os.PathLike[str] | str) -> NoReturn:
        raise error

    monkeypatch.setattr(os, "replace", fail_replace)

    with pytest.raises(OSError, match="replacement failed") as caught:
        exercise_call(write_report_json, sample_report(), destination)

    assert caught.value is error
    assert destination.read_bytes() == b"original-report"
    assert neighbor.read_bytes() == b"unrelated"
    assert {path.name for path in tmp_path.iterdir()} == {"report.json", "keep.tmp"}
