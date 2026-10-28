"""The family must not shrink after looking at its p-values."""

import math

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import bonferroni_rejections

pytestmark = pytest.mark.student_exercise


def test_preserves_original_indexes_and_uses_the_whole_family() -> None:
    values = [0.02, 0.001, 0.8, 0.009, 0.5]
    assert exercise_call(bonferroni_rejections, values) == (1, 3)
    assert values == [0.02, 0.001, 0.8, 0.009, 0.5]


def test_boundary_and_single_hypothesis() -> None:
    assert exercise_call(bonferroni_rejections, [0.025, 0.026]) == (0,)
    assert exercise_call(bonferroni_rejections, [0.05]) == (0,)
    assert exercise_call(bonferroni_rejections, [1.0, 0.0], 0.1) == (1,)
    assert exercise_call(bonferroni_rejections, [0.5, 0.8]) == ()


@pytest.mark.parametrize("values", [[], [-0.1], [1.01], [math.nan], [math.inf], [0.0, math.nan]])
def test_rejects_invalid_whole_family(values: list[float]) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(bonferroni_rejections, values)


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1, math.nan, math.inf])
def test_rejects_invalid_family_alpha(alpha: float) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(bonferroni_rejections, [0.01], alpha)
