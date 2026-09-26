"""Partition repeated sensor observations without sharing a sensor across sets."""

import pandas as pd


def split_sensor_groups(
    frame: pd.DataFrame,
    group_column: str,
    train_fraction: float,
    validation_fraction: float,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return independent train/validation/test copies using whole sensor groups.

    Follow the README's deterministic group permutation and validation contract.
    Preserve source row order, columns, dtypes and original (possibly duplicate) indexes.
    """
    raise NotImplementedError("Implement the group-safe sensor split")
