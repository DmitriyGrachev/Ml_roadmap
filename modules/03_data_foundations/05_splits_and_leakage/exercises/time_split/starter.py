"""Starter boundary for a leakage-resistant chronological split."""

from __future__ import annotations

import pandas as pd


def chronological_split(
    frame: pd.DataFrame,
    train_fraction: float,
    validation_fraction: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return stable chronological train, validation, and test partitions.

    Sort a copy of ``frame`` by its required ``timestamp`` column with a stable sort.
    Use ``floor(n * train_fraction)`` rows for train, then
    ``floor(n * validation_fraction)`` rows for validation, and put the remainder in
    test. Require ``0 < train_fraction < 1``, ``0 <= validation_fraction < 1``, and a
    sum below one. Never mutate ``frame``.
    """
    raise NotImplementedError("Implement the chronological data split")
