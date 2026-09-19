"""Starter boundary for an immutable transaction quality report."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

REQUIRED_COLUMNS = frozenset({"id", "amount", "timestamp"})
KNOWN_CATEGORIES = frozenset({"food", "travel", "utilities"})


@dataclass(frozen=True)
class QualityReport:
    """Immutable counts for the documented transaction-quality checks."""

    missing_id_count: int
    duplicate_id_count: int
    invalid_amount_count: int
    invalid_timestamp_count: int
    unknown_category_count: int


def assess_transaction_quality(frame: pd.DataFrame) -> QualityReport:
    """Assess documented quality conditions without mutating `frame`.

    Required columns are `id`, `amount`, and `timestamp`; `category` is optional. Raise
    `ValueError` when a required column is absent. A completed implementation returns a
    `QualityReport` counting blank or null IDs, repeated present IDs after their first
    occurrence, nonpositive/nonfinite/unparseable amounts, invalid or timezone-naive
    timestamps, and present categories outside `KNOWN_CATEGORIES`. Do not mutate `frame`.
    """
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"missing required columns: {sorted(missing_columns)}")
    raise NotImplementedError("Implement transaction quality assessment")
