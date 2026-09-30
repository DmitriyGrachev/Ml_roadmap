"""Learner-owned one-day forecasting boundaries."""

from pathlib import Path

import pandas as pd


def features_at(series: pd.Series, origin: pd.Timestamp) -> pd.DataFrame:
    """One row at origin: lag_1, lag_7, rolling_7, day_of_week; past values only.

    Validate daily contiguous dates and seven available past observations.
    Origin may be the day after the final observation; never read its target.
    """
    # TODO: validate chronology and build the shifted lag/rolling/calendar row.
    raise NotImplementedError("Implement leakage-safe features")


def run_study(output_dir: Path) -> Path:
    """Fit existing sklearn Ridge and compare naive/weekly baselines on shared origins.

    Save actual rolling one-day predictions and a descriptive random-split comparison.
    Refuse an existing output directory. No multi-step or fitted-model provenance claim.
    """
    # TODO: fit only past targets at each origin, evaluate, and save bound evidence.
    raise NotImplementedError("Implement the one-day study")
