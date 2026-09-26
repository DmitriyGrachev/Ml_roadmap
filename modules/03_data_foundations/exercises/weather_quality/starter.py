"""Student boundary for cleaning and summarizing weather observations."""

from dataclasses import dataclass

import pandas as pd

REQUIRED_COLUMNS = frozenset({"station", "day", "temperature_c", "rainfall_mm"})


@dataclass(frozen=True)
class StationSummary:
    """Summary of retained observations for one normalized station."""

    station: str
    observation_count: int
    mean_temperature_c: float
    total_rainfall_mm: float


@dataclass(frozen=True)
class WeatherReport:
    """Quality counts and deterministic station summaries."""

    total_rows: int
    invalid_rows: int
    duplicate_rows: int
    stations: tuple[StationSummary, ...]


def summarize_weather(frame: pd.DataFrame) -> WeatherReport:
    """Validate, deduplicate, and aggregate the documented weather columns."""
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if not frame.columns.is_unique:
        raise ValueError("column names must be unique")
    # TODO: report invalid rows, remove valid duplicate keys, and summarize stations.
    raise NotImplementedError("summarize weather observations")
