"""Starter boundary for a grouped transaction summary."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = frozenset({"currency", "status", "amount", "timestamp"})


def summarize_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize valid transaction rows by currency and status.

    The input requires `currency`, `status`, `amount`, and timestamp-compatible
    `timestamp` columns. Raise `ValueError` for a missing column or an unparseable
    timestamp. Rows missing any required value are excluded. Return sorted `currency`,
    `status`, `transaction_count`, `total_amount`, `median_amount`, and `p95_amount`
    columns with string, string, int64, float64, float64, and float64 dtypes
    respectively. Do not mutate `frame`.
    """
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"missing required columns: {sorted(missing_columns)}")
    try:
        pd.to_datetime(frame["timestamp"], errors="raise", utc=True)
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamp values must be parseable") from exc
    raise NotImplementedError("Implement the grouped transaction summary")
