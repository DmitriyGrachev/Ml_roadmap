"""Behavioral contract for paired, cluster-aware loss comparison."""

import math

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import DifferenceEstimate, paired_difference

pytestmark = pytest.mark.student_exercise


def test_equal_models_have_zero_effect_and_interval() -> None:
    result = exercise_call(
        paired_difference,
        [1.0, 3.0, 2.0],
        [1.0, 3.0, 2.0],
        ["a", "b", "c"],
        seed=7,
        n_resamples=200,
        confidence=0.95,
    )
    assert result == DifferenceEstimate(0.0, 0.0, 0.0, 3, 200)


def test_constant_two_unit_worsening_is_two() -> None:
    result = exercise_call(
        paired_difference,
        [1.0, 3.0],
        [3.0, 5.0],
        ["a", "b"],
        seed=1,
        n_resamples=100,
        confidence=0.8,
    )
    assert result.effect == pytest.approx(2.0)
    assert result.lower == pytest.approx(2.0)
    assert result.upper == pytest.approx(2.0)


def test_unequal_cluster_sizes_get_equal_unit_weight() -> None:
    result = exercise_call(
        paired_difference,
        [0.0] * 5,
        [1.0, 1.0, 1.0, 1.0, 5.0],
        ["first"] * 4 + ["second"],
        seed=2,
        n_resamples=100,
        confidence=0.9,
    )
    assert result.effect == pytest.approx(3.0)
    assert result.unit_count == 2
    assert result.resample_count == 100
    assert result.lower == pytest.approx(1.0)
    assert result.upper == pytest.approx(5.0)


def test_aligned_nonuniform_differences_and_seed_repeat() -> None:
    args = ([2.0, 7.0, 3.0], [4.0, 5.0, 8.0], ["x", "y", "z"])
    first = exercise_call(paired_difference, *args, seed=11, n_resamples=150, confidence=0.9)
    second = exercise_call(paired_difference, *args, seed=11, n_resamples=150, confidence=0.9)
    assert first.effect == pytest.approx(5 / 3)
    assert first == second
    # Independently enumerated seeded resample means and linear percentiles.
    assert first.lower == pytest.approx(-2 / 3)
    assert first.upper == pytest.approx(4.0)
    assert first.unit_count == 3
    assert first.resample_count == 150


@pytest.mark.parametrize(
    ("a", "b", "ids", "seed", "resamples", "confidence"),
    [
        ([1.0], [1.0, 2.0], ["x"], 1, 100, 0.95),
        ([1.0, 2.0], [1.0, 2.0], ["x"], 1, 100, 0.95),
        ([1.0, 2.0], [1.0, 2.0], ["x", "x"], 1, 100, 0.95),
        ([math.nan, 2.0], [1.0, 2.0], ["x", "y"], 1, 100, 0.95),
        ([1.0, 2.0], [math.inf, 2.0], ["x", "y"], 1, 100, 0.95),
        ([1.0, 2.0], [1.0, 2.0], ["x", "y"], 1, 99, 0.95),
        ([1.0, 2.0], [1.0, 2.0], ["x", "y"], 1, 100, 1.0),
        ([1.0, 2.0], [1.0, 2.0], ["x", "y"], 1, 100, 0.0),
    ],
)
def test_invalid_comparison_rejected(
    a: list[float],
    b: list[float],
    ids: list[str],
    seed: int,
    resamples: int,
    confidence: float,
) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(
            paired_difference,
            a,
            b,
            ids,
            seed=seed,
            n_resamples=resamples,
            confidence=confidence,
        )
