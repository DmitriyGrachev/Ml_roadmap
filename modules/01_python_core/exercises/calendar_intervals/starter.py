"""Student boundary for combining a day's calendar intervals."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Interval:
    """A half-open interval measured in whole minutes after midnight."""

    start: int
    end: int


def merge_intervals(intervals: Sequence[Interval]) -> list[Interval]:
    """Return ordered, disjoint busy intervals, joining touching intervals too."""
    for interval in intervals:
        if (
            type(interval.start) is not int
            or type(interval.end) is not int
            or not 0 <= interval.start < interval.end <= 1440
        ):
            raise ValueError("interval endpoints must be integers with 0 <= start < end <= 1440")
    # TODO: combine overlaps, containment, duplicates, and touching boundaries.
    raise NotImplementedError("merge calendar intervals")
