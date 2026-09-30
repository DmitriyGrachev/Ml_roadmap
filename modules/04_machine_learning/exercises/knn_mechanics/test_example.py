"""The scale demonstration is independent of the learner's classifier."""

import pytest

from .example import run_example


def test_unit_change_reorders_distances_without_changing_rows() -> None:
    result = run_example()
    assert result["raw_distances"] == pytest.approx((2.0, 100.00499987500625))
    assert result["converted_distances"] == pytest.approx((2.0, 2**0.5))
    assert result["raw_nearest_row"] == 0
    assert result["converted_nearest_row"] == 1
