"""Student boundary for deterministic weather-alert threshold selection."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ThresholdChoice:
    """The chosen candidate and its validation-set metrics."""

    threshold: float
    precision: float
    recall: float
    alerts: int


def choose_threshold(
    scores: tuple[float, ...],
    actual: tuple[int, ...],
    *,
    thresholds: tuple[float, ...],
    min_recall: float,
    min_precision: float,
) -> ThresholdChoice | None:
    """Select a feasible supplied candidate using the documented tie policy."""
    if len(scores) != len(actual):
        raise ValueError("scores and actual lengths must match")
    if any(type(label) is not int or label not in (0, 1) for label in actual):
        raise ValueError("actual labels must be integer zero or one")
    values = (*scores, *thresholds, min_recall, min_precision)
    if any(
        type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 1
        for value in values
    ):
        raise ValueError("scores, thresholds, and policy bounds must be finite in [0, 1]")
    # TODO: evaluate candidate alerts, enforce bounds, and rank feasible choices.
    raise NotImplementedError("weather-alert threshold policy")
