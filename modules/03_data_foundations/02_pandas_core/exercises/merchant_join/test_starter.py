"""Acceptance tests for the merchant-join student boundary."""

from __future__ import annotations

import pandas as pd
import pytest

from roadmap_tools import exercise_call

from .starter import attach_merchant_risk


def test_attaches_risk_without_dropping_unmatched_rows_or_mutating_inputs() -> None:
    transactions = pd.DataFrame(
        {
            "transaction_id": ["T-3", "T-4", "T-1", "T-2"],
            "merchant_id": ["M-2", "M-404", "M-1", "M-2"],
            "amount": [15.0, 30.0, 20.0, 25.0],
        }
    )
    merchants = pd.DataFrame(
        {
            "merchant_id": ["M-1", "M-2"],
            "risk_band": ["low", "high"],
        }
    )
    original_transactions = transactions.copy(deep=True)
    original_merchants = merchants.copy(deep=True)

    attached = exercise_call(attach_merchant_risk, transactions, merchants)

    expected = pd.DataFrame(
        {
            "transaction_id": ["T-3", "T-4", "T-1", "T-2"],
            "merchant_id": ["M-2", "M-404", "M-1", "M-2"],
            "amount": [15.0, 30.0, 20.0, 25.0],
            "risk_band": ["high", float("nan"), "low", "high"],
        }
    )
    pd.testing.assert_frame_equal(attached, expected)
    assert len(attached) == len(transactions)
    pd.testing.assert_frame_equal(transactions, original_transactions)
    pd.testing.assert_frame_equal(merchants, original_merchants)


def test_rejects_duplicate_merchant_keys_during_exercise_acceptance() -> None:
    transactions = pd.DataFrame(
        {"transaction_id": ["T-1"], "merchant_id": ["M-1"], "amount": [10.0]}
    )
    merchants = pd.DataFrame({"merchant_id": ["M-1", "M-1"], "risk_band": ["low", "high"]})

    with pytest.raises(ValueError, match=r"duplicate merchant|not unique|many-to-one"):
        exercise_call(attach_merchant_risk, transactions, merchants)


@pytest.mark.parametrize(
    ("transactions", "merchants"),
    [
        (
            pd.DataFrame({"merchant_id": ["M-1"]}),
            pd.DataFrame({"merchant_id": ["M-1"], "risk_band": ["low"]}),
        ),
        (
            pd.DataFrame({"transaction_id": ["T-1"], "merchant_id": ["M-1"], "amount": [1.0]}),
            pd.DataFrame({"merchant_id": ["M-1"]}),
        ),
    ],
)
def test_rejects_missing_required_columns(
    transactions: pd.DataFrame, merchants: pd.DataFrame
) -> None:
    with pytest.raises(ValueError, match="required"):
        attach_merchant_risk(transactions, merchants)
