"""Learner-owned temporal aggregation boundary."""

import pandas as pd


def build_point_in_time_features(
    events: pd.DataFrame, queries: pd.DataFrame, window: pd.Timedelta
) -> pd.DataFrame:
    """Return query_id/count/sum/mean in query row order over [as_of-window, as_of)."""
    raise NotImplementedError("Implement entity-isolated, UTC point-in-time features")
