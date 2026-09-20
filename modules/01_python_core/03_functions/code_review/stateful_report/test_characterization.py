"""Characterization tests for the stateful report-builder review fixture."""

from copy import deepcopy
from decimal import Decimal

from .review_me import MerchantTotal, ReportBuilder, ReportRow


def test_build_preserves_first_seen_merchant_order_and_decimal_totals() -> None:
    rows: list[ReportRow] = [
        {"transaction_id": "txn-001", "merchant": "Bakery", "amount": Decimal("2.10")},
        {"transaction_id": "txn-002", "merchant": "Cinema", "amount": Decimal("7.00")},
        {"transaction_id": "txn-003", "merchant": "Bakery", "amount": Decimal("0.30")},
    ]

    assert ReportBuilder().build(rows) == (
        MerchantTotal(merchant="Bakery", total=Decimal("2.40")),
        MerchantTotal(merchant="Cinema", total=Decimal("7.00")),
    )


def test_repeated_builds_do_not_leak_previous_report_state() -> None:
    builder = ReportBuilder()

    first_report = builder.build(
        [{"transaction_id": "txn-004", "merchant": "Cafe", "amount": Decimal("4.50")}]
    )
    second_report = builder.build(
        [{"transaction_id": "txn-005", "merchant": "Market", "amount": Decimal("9.25")}]
    )

    assert first_report == (MerchantTotal(merchant="Cafe", total=Decimal("4.50")),)
    assert second_report == (MerchantTotal(merchant="Market", total=Decimal("9.25")),)


def test_empty_build_after_populated_build_returns_an_empty_report() -> None:
    builder = ReportBuilder()
    builder.build(
        [{"transaction_id": "txn-006", "merchant": "Pharmacy", "amount": Decimal("1.20")}]
    )

    assert builder.build([]) == ()


def test_build_does_not_mutate_nested_input_rows() -> None:
    rows: list[ReportRow] = [
        {"transaction_id": "txn-007", "merchant": "Station", "amount": Decimal("5.00")}
    ]
    original_rows = deepcopy(rows)

    ReportBuilder().build(rows)

    assert rows == original_rows
