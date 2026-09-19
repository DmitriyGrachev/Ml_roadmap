"""Starter boundary for a cardinality-safe merchant-risk join."""

from __future__ import annotations

import pandas as pd

TRANSACTION_COLUMNS = frozenset({"transaction_id", "merchant_id", "amount"})
MERCHANT_COLUMNS = frozenset({"merchant_id", "risk_band"})


def attach_merchant_risk(transactions: pd.DataFrame, merchants: pd.DataFrame) -> pd.DataFrame:
    """Attach one merchant risk band to each transaction without changing inputs.

    Transactions require `transaction_id`, `merchant_id`, and `amount`; merchants
    require `merchant_id` and `risk_band`. Reject missing columns and duplicate merchant
    keys with `ValueError`. The completed solution must preserve transaction row count
    and left-row order while using a many-to-one merge.
    """
    missing_transactions = TRANSACTION_COLUMNS.difference(transactions.columns)
    if missing_transactions:
        raise ValueError(f"transactions missing required columns: {sorted(missing_transactions)}")
    missing_merchants = MERCHANT_COLUMNS.difference(merchants.columns)
    if missing_merchants:
        raise ValueError(f"merchants missing required columns: {sorted(missing_merchants)}")
    if merchants["merchant_id"].duplicated().any():
        raise ValueError("duplicate merchant keys are not allowed")
    raise NotImplementedError("Implement a cardinality-safe merchant risk join")
