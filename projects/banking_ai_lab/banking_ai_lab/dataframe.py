"""Stage 3 Pandas contracts with intentionally unfinished student operations."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from banking_ai_lab.domain import Transaction


def transaction_frame(transactions: Iterable[Transaction]) -> pd.DataFrame:
    """Return transactions in the documented stable Pandas schema."""
    raise NotImplementedError("convert transactions to a stable DataFrame")


def daily_currency_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transaction count, amount, and fraud count by UTC day and currency."""
    raise NotImplementedError("summarize the transaction frame by UTC day and currency")
