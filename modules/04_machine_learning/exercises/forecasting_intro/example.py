"""Separate four-day temperature example; no feature builder or study solution."""

from itertools import pairwise


def previous_day_error() -> float:
    observed_temperatures = [8.0, 10.0, 14.0, 11.0]
    errors = [abs(today - yesterday) for yesterday, today in pairwise(observed_temperatures)]
    return sum(errors) / len(errors)
