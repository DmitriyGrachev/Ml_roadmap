"""Stage 3 Pandas-boundary acceptance contracts."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pandas as pd
import pytest
from banking_ai_lab.dataframe import daily_currency_summary, transaction_frame
from banking_ai_lab.domain import CURRENCIES, STATUSES, TRANSACTION_COLUMNS, Transaction

from roadmap_tools import exercise_call

SUMMARY_COLUMNS = (
    "day",
    "currency",
    "transaction_count",
    "total_amount",
    "fraud_count",
)


def make_transaction(
    index: int,
    *,
    amount: str = "10.25",
    currency: str = "EUR",
    merchant: str = "Aurora Market",
    category: str | None = "groceries",
    timestamp: datetime | None = None,
    status: str = "approved",
    is_fraud: bool = False,
) -> Transaction:
    return Transaction.model_validate(
        {
            "id": UUID(int=index),
            "user_id": f"user-{index:04d}",
            "amount": Decimal(amount),
            "currency": currency,
            "merchant": merchant,
            "category": category,
            "timestamp": timestamp or datetime(2025, 1, index, 10, tzinfo=UTC),
            "status": status,
            "is_fraud": is_fraud,
        }
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


def assert_transaction_dtypes(frame: pd.DataFrame) -> None:
    assert isinstance(frame.dtypes["id"], pd.StringDtype)
    assert isinstance(frame.dtypes["user_id"], pd.StringDtype)
    assert str(frame.dtypes["amount"]) == "float64"
    assert isinstance(frame.dtypes["currency"], pd.CategoricalDtype)
    assert isinstance(frame.dtypes["merchant"], pd.StringDtype)
    assert isinstance(frame.dtypes["category"], pd.CategoricalDtype)
    assert str(frame.dtypes["timestamp"]) == "datetime64[ns, UTC]"
    assert isinstance(frame.dtypes["status"], pd.CategoricalDtype)
    assert str(frame.dtypes["is_fraud"]) == "bool"


def empty_transaction_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": pd.Series([], dtype="string[python]"),
            "user_id": pd.Series([], dtype="string[python]"),
            "amount": pd.Series([], dtype="float64"),
            "currency": pd.Series(pd.Categorical([], categories=CURRENCIES)),
            "merchant": pd.Series([], dtype="string[python]"),
            "category": pd.Series(pd.Categorical([])),
            "timestamp": pd.Series([], dtype="datetime64[ns, UTC]"),
            "status": pd.Series(pd.Categorical([], categories=STATUSES)),
            "is_fraud": pd.Series([], dtype="bool"),
        }
    )


def populated_transaction_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": pd.Series(
                [str(UUID(int=index)) for index in (1, 2, 3, 4)], dtype="string[python]"
            ),
            "user_id": pd.Series(
                ["user-0001", "user-0002", "user-0003", "user-0004"], dtype="string[python]"
            ),
            "amount": pd.Series([5.25, 10.25, 7.0, 0.5], dtype="float64"),
            "currency": pd.Series(
                pd.Categorical(["USD", "EUR", "EUR", "USD"], categories=CURRENCIES)
            ),
            "merchant": pd.Series(["Delta", "Aurora", "Beta", "Cedar"], dtype="string[python]"),
            "category": pd.Series(pd.Categorical(["travel", "groceries", "health", None])),
            "timestamp": pd.Series(
                pd.to_datetime(
                    [
                        "2025-01-01T11:00:00Z",
                        "2025-01-01T10:00:00Z",
                        "2025-01-02T09:00:00Z",
                        "2025-01-01T12:00:00Z",
                    ],
                    utc=True,
                ),
                dtype="datetime64[ns, UTC]",
            ),
            "status": pd.Series(pd.Categorical(["approved"] * 4, categories=STATUSES)),
            "is_fraud": pd.Series([False, True, False, True], dtype="bool"),
        }
    )


def empty_summary_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "day": pd.Series([], dtype="datetime64[ns, UTC]"),
            "currency": pd.Series([], dtype="string[python]"),
            "transaction_count": pd.Series([], dtype="int64"),
            "total_amount": pd.Series([], dtype="float64"),
            "fraud_count": pd.Series([], dtype="int64"),
        }
    )


@pytest.mark.student_exercise
def test_transaction_frame_has_exact_columns_values_and_stable_dtypes() -> None:
    first = make_transaction(1, amount="0.10", currency="USD", category=None, is_fraud=True)
    second = make_transaction(2, amount="2.25", currency="EUR", merchant="Café Aurora")

    frame = exercise_call(transaction_frame, [first, second])

    assert tuple(frame.columns) == TRANSACTION_COLUMNS
    assert_transaction_dtypes(frame)
    assert frame["id"].tolist() == [str(first.id), str(second.id)]
    assert frame["user_id"].tolist() == [first.user_id, second.user_id]
    assert frame["amount"].tolist() == [0.10, 2.25]
    assert frame["merchant"].tolist() == [first.merchant, second.merchant]
    assert pd.isna(frame.loc[0, "category"])
    assert frame.loc[1, "category"] == "groceries"
    assert frame["is_fraud"].tolist() == [True, False]


@pytest.mark.student_exercise
def test_transaction_frame_keeps_supported_category_orders_and_utc_resolution() -> None:
    transactions = [
        make_transaction(
            1,
            currency="USD",
            category="travel",
            timestamp=datetime(2025, 2, 3, 15, 45, tzinfo=UTC),
            status="refunded",
        ),
        make_transaction(
            2,
            currency="EUR",
            category="groceries",
            timestamp=datetime(2025, 1, 4, 8, 30, tzinfo=UTC),
            status="approved",
        ),
    ]

    frame = exercise_call(transaction_frame, transactions)

    assert tuple(frame["currency"].cat.categories) == CURRENCIES
    assert tuple(frame["status"].cat.categories) == STATUSES
    assert tuple(frame["category"].cat.categories) == ("groceries", "travel")
    assert str(frame["timestamp"].dtype) == "datetime64[ns, UTC]"
    assert frame["currency"].tolist() == ["USD", "EUR"]
    assert frame["status"].tolist() == ["refunded", "approved"]
    assert frame["timestamp"].tolist() == [
        pd.Timestamp(transaction.timestamp) for transaction in transactions
    ]


@pytest.mark.student_exercise
def test_transaction_frame_has_the_same_empty_schema() -> None:
    frame = exercise_call(transaction_frame, iter(()))

    assert tuple(frame.columns) == TRANSACTION_COLUMNS
    assert frame.empty
    assert_transaction_dtypes(frame)
    assert tuple(frame["currency"].cat.categories) == CURRENCIES
    assert tuple(frame["status"].cat.categories) == STATUSES
    assert tuple(frame["category"].cat.categories) == ()


@pytest.mark.student_exercise
def test_transaction_frame_consumes_a_one_shot_iterable_once() -> None:
    source = OneShotTransactions([make_transaction(1), make_transaction(2)])

    frame = exercise_call(transaction_frame, source)

    assert len(frame) == 2


@pytest.mark.student_exercise
def test_transaction_frame_does_not_reorder_or_replace_domain_objects() -> None:
    transactions = [make_transaction(2), make_transaction(1)]
    original_order = tuple(transactions)
    original_ids = tuple(id(item) for item in transactions)

    exercise_call(transaction_frame, transactions)

    assert tuple(transactions) == original_order
    assert tuple(id(item) for item in transactions) == original_ids


@pytest.mark.student_exercise
def test_daily_currency_summary_returns_named_aggregates_in_stable_order() -> None:
    frame = populated_transaction_frame()

    summary = exercise_call(daily_currency_summary, frame)

    expected = pd.DataFrame(
        {
            "day": pd.Series(
                pd.to_datetime(
                    ["2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z"],
                    utc=True,
                ),
                dtype="datetime64[ns, UTC]",
            ),
            "currency": pd.Series(["EUR", "USD", "EUR"], dtype="string[python]"),
            "transaction_count": pd.Series([1, 2, 1], dtype="int64"),
            "total_amount": pd.Series([10.25, 5.75, 7.0], dtype="float64"),
            "fraud_count": pd.Series([1, 1, 0], dtype="int64"),
        }
    )
    pd.testing.assert_frame_equal(summary, expected)


@pytest.mark.student_exercise
def test_daily_currency_summary_keeps_a_stable_empty_schema() -> None:
    summary = exercise_call(daily_currency_summary, empty_transaction_frame())

    pd.testing.assert_frame_equal(summary, empty_summary_frame())
    assert tuple(summary.columns) == SUMMARY_COLUMNS


@pytest.mark.student_exercise
def test_daily_currency_summary_does_not_mutate_the_input_frame() -> None:
    frame = populated_transaction_frame()
    before = frame.copy(deep=True)

    exercise_call(daily_currency_summary, frame)

    pd.testing.assert_frame_equal(frame, before)
