"""Small deterministic daily demand fixture; no downloads or hidden fitted model."""

import json

import numpy as np
import pandas as pd


def daily_counts() -> pd.Series:
    days = pd.date_range("2024-01-01", periods=84, freq="D")
    counts = [20 + (day // 21) * 3 + (8 if day % 7 in (5, 6) else 0) + day % 3 for day in range(84)]
    return pd.Series(counts, index=days, name="count", dtype="float64")


def dataset_bytes() -> bytes:
    series = daily_counts()
    return (
        json.dumps(
            [
                {"date": str(date.date()), "count": int(value)}
                for date, value in zip(series.index, series.tolist(), strict=True)
            ],
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


def validate_series(series: pd.Series) -> None:
    if (
        not isinstance(series.index, pd.DatetimeIndex)
        or len(series) < 2
        or series.index.tz is not None
        or not series.index.equals(pd.date_range(series.index[0], periods=len(series), freq="D"))
        or not series.index.equals(series.index.normalize())
        or not np.isfinite(series.to_numpy(dtype=float)).all()
        or (series < 0).any()
    ):
        raise ValueError("series must have finite nonnegative counts on contiguous daily dates")
