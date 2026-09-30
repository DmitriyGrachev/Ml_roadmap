"""A/A and A/B demo uses object assignments and a fixed observation horizon."""

import pytest

from .example import run_example


def test_demo_repeats_assignments_by_object_and_is_reproducible() -> None:
    first = run_example(seed=21)
    second = run_example(seed=21)
    assert first == second
    assert first["units"] == 24
    assert first["events_per_unit"] == 3
    assert first["a_units"] + first["b_units"] == 24
    assert first["a_units"] > 0
    assert first["b_units"] > 0
    assert isinstance(first["aa_difference"], float)
    assert isinstance(first["ab_difference"], float)
    assert first["ab_difference"] == pytest.approx(first["aa_difference"] + 0.4)
