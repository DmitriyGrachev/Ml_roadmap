"""The example demonstrates alignment only, on unrelated temperatures."""

from .example import previous_day_error


def test_temperature_previous_day_alignment() -> None:
    assert previous_day_error() == 3.0
