"""Starter boundaries for fraud confusion counts and derived metrics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfusionCounts:
    """Immutable binary-classification counts, with fraud as the positive class."""

    tp: int
    fp: int
    tn: int
    fn: int


def confusion_counts(labels: Sequence[int], predictions: Sequence[int]) -> ConfusionCounts:
    """Count binary labels and predictions, rejecting mismatched or invalid inputs."""
    raise NotImplementedError("Implement binary confusion counts")


def accuracy(counts: ConfusionCounts, *, zero_division: float = 0.0) -> float:
    """Return accuracy, or ``zero_division`` when no observations are counted."""
    raise NotImplementedError("Implement accuracy from confusion counts")


def precision(counts: ConfusionCounts, *, zero_division: float = 0.0) -> float:
    """Return precision, or ``zero_division`` when no positive prediction exists."""
    raise NotImplementedError("Implement precision from confusion counts")


def recall(counts: ConfusionCounts, *, zero_division: float = 0.0) -> float:
    """Return recall, or ``zero_division`` when no actual positive exists."""
    raise NotImplementedError("Implement recall from confusion counts")


def f1(counts: ConfusionCounts, *, zero_division: float = 0.0) -> float:
    """Return F1, or ``zero_division`` when no actual or predicted positive exists."""
    raise NotImplementedError("Implement F1 from confusion counts")
