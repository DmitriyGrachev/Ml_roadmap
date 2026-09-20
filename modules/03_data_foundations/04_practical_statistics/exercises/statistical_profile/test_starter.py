"""Acceptance tests for the statistical-profile student boundary."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import numpy as np
import pytest

from roadmap_tools import exercise_call

from .starter import StatisticalProfile, describe_amounts


def test_statistical_profile_has_the_documented_immutable_schema() -> None:
    assert [field.name for field in fields(StatisticalProfile)] == [
        "mean",
        "median",
        "variance",
        "standard_deviation",
        "p25",
        "p75",
        "p95",
    ]
    profile = StatisticalProfile(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    field_name = "mean"

    with pytest.raises(FrozenInstanceError):
        setattr(profile, field_name, 1.0)


def test_outlier_moves_the_mean_more_than_the_median_without_mutating_input() -> None:
    values = np.array([1.0, 2.0, 3.0, 100.0], dtype=np.float64)
    original = values.copy()

    profile = exercise_call(describe_amounts, values)

    assert profile.mean == pytest.approx(26.5)
    assert profile.median == pytest.approx(2.5)
    assert profile.mean > profile.median
    np.testing.assert_array_equal(values, original)


def test_uses_population_variance_and_standard_deviation() -> None:
    values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)

    profile = exercise_call(describe_amounts, values)

    assert profile.variance == pytest.approx(1.25)
    assert profile.standard_deviation == pytest.approx(1.118033988749895)


def test_reports_selected_percentiles_with_linear_interpolation() -> None:
    values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)

    profile = exercise_call(describe_amounts, values)

    assert profile.p25 == pytest.approx(1.75)
    assert profile.p75 == pytest.approx(3.25)
    assert profile.p95 == pytest.approx(3.85)


def test_ignores_nan_values_when_finite_values_remain() -> None:
    values = np.array([1.0, np.nan, 3.0], dtype=np.float64)

    profile = exercise_call(describe_amounts, values)

    assert profile.mean == pytest.approx(2.0)
    assert profile.median == pytest.approx(2.0)
    assert profile.variance == pytest.approx(1.0)
    assert profile.standard_deviation == pytest.approx(1.0)
    assert profile.p25 == pytest.approx(1.5)
    assert profile.p75 == pytest.approx(2.5)
    assert profile.p95 == pytest.approx(2.9)


def test_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match=r"empty|value"):
        exercise_call(describe_amounts, np.array([], dtype=np.float64))


def test_rejects_all_nan_input() -> None:
    with pytest.raises(ValueError, match=r"NaN|finite|value"):
        exercise_call(describe_amounts, np.array([np.nan, np.nan], dtype=np.float64))


@pytest.mark.parametrize("nonfinite", [np.inf, -np.inf])
def test_rejects_infinite_values(nonfinite: float) -> None:
    with pytest.raises(ValueError, match=r"finite|infinity|value"):
        exercise_call(
            describe_amounts,
            np.array([1.0, nonfinite], dtype=np.float64),
        )
