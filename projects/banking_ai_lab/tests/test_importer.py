"""Domain infrastructure and Stage 1 CSV-import acceptance contracts."""

from __future__ import annotations

import csv
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest
from banking_ai_lab.domain import (
    CATEGORY_MAX_LENGTH,
    MERCHANT_MAX_LENGTH,
    TRANSACTION_COLUMNS,
    USER_ID_MAX_LENGTH,
    Transaction,
)
from banking_ai_lab.importer import ImportIssue, ImportResult, import_transactions
from pydantic import ValidationError

from roadmap_tools import exercise_call

REPOSITORY_ROOT = Path(__file__).parents[3]


def transaction_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "0f70c8d6-0ea8-5cd6-831d-4ef840d4fa60",
        "user_id": "user-0042",
        "amount": Decimal("10.25"),
        "currency": "EUR",
        "merchant": "Aurora Market",
        "category": "groceries",
        "timestamp": datetime(2025, 1, 2, 12, 30, tzinfo=UTC),
        "status": "approved",
        "is_fraud": False,
    }
    payload.update(overrides)
    return payload


def csv_row(index: int, **overrides: str) -> dict[str, str]:
    row = {
        "id": str(UUID(int=index)),
        "user_id": f"user-{index:04d}",
        "amount": "10.25",
        "currency": "EUR",
        "merchant": "Aurora Market",
        "category": "groceries",
        "timestamp": f"2025-01-{index:02d}T10:00:00+00:00",
        "status": "approved",
        "is_fraud": "false",
    }
    row.update(overrides)
    return row


def write_csv(
    path: Path,
    rows: list[dict[str, str]],
    *,
    fieldnames: tuple[str, ...] = TRANSACTION_COLUMNS,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_transaction_normalizes_aware_timestamps_and_hides_the_user_identifier() -> None:
    offset = timezone(timedelta(hours=2))
    transaction = Transaction.model_validate(
        transaction_payload(timestamp=datetime(2025, 1, 2, 12, 30, tzinfo=offset))
    )

    assert transaction.id == UUID("0f70c8d6-0ea8-5cd6-831d-4ef840d4fa60")
    assert transaction.amount == Decimal("10.25")
    assert transaction.timestamp == datetime(2025, 1, 2, 10, 30, tzinfo=UTC)
    assert transaction.timestamp.tzinfo is UTC
    assert "user-0042" not in repr(transaction)


def test_transaction_accepts_an_absent_category() -> None:
    transaction = Transaction.model_validate(transaction_payload(category=None))

    assert transaction.category is None


@pytest.mark.parametrize(
    ("field", "maximum"),
    [
        ("user_id", USER_ID_MAX_LENGTH),
        ("merchant", MERCHANT_MAX_LENGTH),
        ("category", CATEGORY_MAX_LENGTH),
    ],
)
def test_transaction_text_width_matches_the_persistence_schema(
    field: str,
    maximum: int,
) -> None:
    accepted = "x" * maximum
    transaction = Transaction.model_validate(transaction_payload(**{field: accepted}))

    assert getattr(transaction, field) == accepted
    with pytest.raises(ValidationError) as caught:
        Transaction.model_validate(transaction_payload(**{field: "x" * (maximum + 1)}))

    assert [error["loc"] for error in caught.value.errors()] == [(field,)]


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0"),
        Decimal("-0.01"),
        Decimal("1.001"),
        Decimal("NaN"),
        Decimal("Infinity"),
        1.25,
        True,
    ],
)
def test_transaction_rejects_non_positive_non_finite_or_imprecise_amounts(
    amount: object,
) -> None:
    with pytest.raises(ValidationError):
        Transaction.model_validate(transaction_payload(amount=amount))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("user_id", ""),
        ("user_id", "   "),
        ("merchant", ""),
        ("merchant", "   "),
        ("category", ""),
        ("category", "   "),
    ],
)
def test_transaction_rejects_blank_text_fields(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        Transaction.model_validate(transaction_payload(**{field: value}))


@pytest.mark.parametrize(
    ("field", "value"),
    [("currency", "CAD"), ("currency", "eur"), ("status", "unknown")],
)
def test_transaction_rejects_unsupported_currency_and_status(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        Transaction.model_validate(transaction_payload(**{field: value}))


def test_transaction_rejects_a_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        Transaction.model_validate(transaction_payload(timestamp=datetime(2025, 1, 2, 12, 30)))


def test_transaction_is_frozen() -> None:
    transaction = Transaction.model_validate(transaction_payload())

    with pytest.raises(ValidationError):
        cast(Any, transaction).merchant = "Changed Merchant"


def test_transaction_validation_message_does_not_echo_sensitive_row_values() -> None:
    payload = transaction_payload(
        user_id="user-sensitive-9999",
        merchant="Sensitive Merchant Token",
        amount="not-a-decimal",
    )

    with pytest.raises(ValidationError) as caught:
        Transaction.model_validate(payload)

    message = str(caught.value)
    assert "user-sensitive-9999" not in message
    assert "Sensitive Merchant Token" not in message
    assert str(payload) not in message


def test_import_records_are_frozen_and_copy_caller_owned_collections() -> None:
    transaction = Transaction.model_validate(transaction_payload())
    issue = ImportIssue(row_number=2, field="amount", message="invalid amount")
    source_transactions = [transaction]
    source_issues = [issue]

    result = ImportResult(transactions=source_transactions, issues=source_issues)  # type: ignore[arg-type]
    source_transactions.clear()
    source_issues.clear()

    assert result.transactions == (transaction,)
    assert result.issues == (issue,)
    with pytest.raises(FrozenInstanceError):
        cast(Any, issue).field = "status"
    with pytest.raises(FrozenInstanceError):
        cast(Any, result).transactions = ()


@pytest.mark.student_exercise
def test_import_transactions_preserves_clean_rows_in_file_order(tmp_path: Path) -> None:
    path = tmp_path / "transactions.csv"
    rows = [
        csv_row(1, amount="0.10", category=""),
        csv_row(2, amount="123.45", currency="USD", is_fraud="true"),
    ]
    write_csv(path, rows)

    result = exercise_call(import_transactions, path)

    assert result.issues == ()
    assert [str(item.id) for item in result.transactions] == [rows[0]["id"], rows[1]["id"]]
    assert [item.amount for item in result.transactions] == [Decimal("0.10"), Decimal("123.45")]
    assert [item.category for item in result.transactions] == [None, "groceries"]
    assert [item.is_fraud for item in result.transactions] == [False, True]


@pytest.mark.student_exercise
def test_import_transactions_accepts_the_generated_repository_dataset() -> None:
    result = exercise_call(import_transactions, REPOSITORY_ROOT / "datasets" / "transactions.csv")

    assert len(result.transactions) == 1_000
    assert result.issues == ()


@pytest.mark.student_exercise
def test_import_transactions_raises_for_a_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        exercise_call(import_transactions, missing)


@pytest.mark.student_exercise
def test_import_transactions_reports_every_header_for_an_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_bytes(b"")

    result = exercise_call(import_transactions, path)

    assert result.transactions == ()
    assert result.issues == tuple(
        ImportIssue(row_number=0, field=field, message="required header is missing")
        for field in TRANSACTION_COLUMNS
    )


@pytest.mark.student_exercise
def test_import_transactions_reports_missing_headers_in_canonical_order(tmp_path: Path) -> None:
    path = tmp_path / "missing-headers.csv"
    present = ("status", "id", "amount")
    write_csv(path, [], fieldnames=present)

    result = exercise_call(import_transactions, path)

    assert result.transactions == ()
    assert result.issues == tuple(
        ImportIssue(row_number=0, field=field, message="required header is missing")
        for field in TRANSACTION_COLUMNS
        if field not in present
    )


@pytest.mark.student_exercise
def test_import_transactions_collects_safe_field_issues_and_continues(tmp_path: Path) -> None:
    path = tmp_path / "mixed.csv"
    invalid = csv_row(
        2,
        user_id="user-sensitive-8888",
        amount="1.234",
        currency="CAD",
        merchant="Sensitive Merchant Token",
        timestamp="2025-01-02T10:00:00",
        status="unknown",
        is_fraud="yes",
    )
    rows = [csv_row(1), invalid, csv_row(3)]
    write_csv(path, rows)

    result = exercise_call(import_transactions, path)

    assert [str(item.id) for item in result.transactions] == [rows[0]["id"], rows[2]["id"]]
    assert [(issue.row_number, issue.field) for issue in result.issues] == [
        (2, "amount"),
        (2, "currency"),
        (2, "timestamp"),
        (2, "status"),
        (2, "is_fraud"),
    ]
    serialized_row = ",".join(invalid.values())
    for issue in result.issues:
        assert issue.message
        assert "user-sensitive-8888" not in issue.message
        assert "Sensitive Merchant Token" not in issue.message
        assert invalid["id"] not in issue.message
        assert serialized_row not in issue.message


@pytest.mark.student_exercise
def test_import_transactions_reports_overlong_text_fields_without_echoing_values(
    tmp_path: Path,
) -> None:
    path = tmp_path / "overlong-text.csv"
    invalid = csv_row(
        1,
        user_id="u" * (USER_ID_MAX_LENGTH + 1),
        merchant="m" * (MERCHANT_MAX_LENGTH + 1),
        category="c" * (CATEGORY_MAX_LENGTH + 1),
    )
    valid = csv_row(2)
    write_csv(path, [invalid, valid])

    result = exercise_call(import_transactions, path)

    assert [str(item.id) for item in result.transactions] == [valid["id"]]
    assert [(issue.row_number, issue.field) for issue in result.issues] == [
        (1, "user_id"),
        (1, "merchant"),
        (1, "category"),
    ]
    for issue in result.issues:
        assert issue.message
        assert invalid[issue.field] not in issue.message


@pytest.mark.student_exercise
def test_import_transactions_orders_field_issues_by_reordered_csv_columns(tmp_path: Path) -> None:
    path = tmp_path / "reordered-columns.csv"
    fieldnames = (
        "status",
        "amount",
        "id",
        "timestamp",
        "currency",
        "user_id",
        "merchant",
        "category",
        "is_fraud",
    )
    write_csv(
        path,
        [
            csv_row(
                1,
                status="unknown",
                amount="1.234",
                timestamp="2025-01-01T10:00:00",
                currency="CAD",
                is_fraud="yes",
            )
        ],
        fieldnames=fieldnames,
    )

    result = exercise_call(import_transactions, path)

    assert result.transactions == ()
    assert [(issue.row_number, issue.field) for issue in result.issues] == [
        (1, "status"),
        (1, "amount"),
        (1, "timestamp"),
        (1, "currency"),
        (1, "is_fraud"),
    ]


@pytest.mark.student_exercise
def test_import_transactions_rejects_excess_decimal_scale_without_rounding(tmp_path: Path) -> None:
    path = tmp_path / "precision.csv"
    write_csv(path, [csv_row(1, amount="1.239")])

    result = exercise_call(import_transactions, path)

    assert result.transactions == ()
    assert [(issue.row_number, issue.field) for issue in result.issues] == [(1, "amount")]


@pytest.mark.student_exercise
def test_import_transactions_distinguishes_exact_rows_from_reused_ids(tmp_path: Path) -> None:
    path = tmp_path / "duplicates.csv"
    first = csv_row(1)
    exact_duplicate = first.copy()
    reused_id = first | {"amount": "99.99", "merchant": "Bluebird Travel"}
    final = csv_row(2)
    write_csv(path, [first, exact_duplicate, reused_id, final])

    result = exercise_call(import_transactions, path)

    assert [str(item.id) for item in result.transactions] == [first["id"], final["id"]]
    assert result.issues == (
        ImportIssue(row_number=2, field="row", message="duplicate row"),
        ImportIssue(row_number=3, field="id", message="duplicate transaction ID"),
    )


@pytest.mark.student_exercise
def test_import_transactions_orders_duplicate_and_field_issues_by_row(tmp_path: Path) -> None:
    path = tmp_path / "ordered-issues.csv"
    first = csv_row(1)
    invalid = csv_row(2, amount="bad", status="unknown")
    write_csv(path, [first, first.copy(), invalid, first | {"amount": "11.00"}])

    result = exercise_call(import_transactions, path)

    assert [(issue.row_number, issue.field) for issue in result.issues] == [
        (2, "row"),
        (3, "amount"),
        (3, "status"),
        (4, "id"),
    ]
