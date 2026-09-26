"""Missing pairs and constant measurements need explicit statistical semantics."""

import math

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import PairSummary, summarize_pairs

pytestmark = pytest.mark.student_exercise


def test_uses_sample_covariance_and_pearson_correlation() -> None:
    result = exercise_call(summarize_pairs, [1.0, 2.0, 4.0], [2.0, 1.0, 5.0])
    assert result.count == 3
    assert result.mean_x == pytest.approx(7 / 3)
    assert result.mean_y == pytest.approx(8 / 3)
    assert result.covariance == pytest.approx(8 / 3)
    assert result.correlation == pytest.approx(8 / math.sqrt(91))


def test_removes_entire_pair_if_either_side_is_nonfinite() -> None:
    result = exercise_call(
        summarize_pairs, [1.0, math.nan, 3.0, math.inf, 5.0], [2.0, 99.0, math.inf, 4.0, 10.0]
    )
    assert result.count == 2
    assert result.mean_x == pytest.approx(3.0)
    assert result.mean_y == pytest.approx(6.0)
    assert result.covariance == pytest.approx(16.0)
    assert result.correlation == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("xs", "ys"), [([], []), ([math.nan], [1.0]), ([1.0, math.inf], [math.inf, 1.0])]
)
def test_no_finite_pairs(xs: list[float], ys: list[float]) -> None:
    assert exercise_call(summarize_pairs, xs, ys) == PairSummary(0, None, None, None, None)


def test_one_pair_has_means_but_no_covariance_or_correlation() -> None:
    assert exercise_call(summarize_pairs, [4.0], [7.0]) == PairSummary(1, 4.0, 7.0, None, None)


@pytest.mark.parametrize(
    ("xs", "ys"), [([2.0, 2.0], [3.0, 5.0]), ([3.0, 5.0], [2.0, 2.0]), ([2.0, 2.0], [2.0, 2.0])]
)
def test_constant_axis_has_zero_covariance_and_undefined_correlation(
    xs: list[float], ys: list[float]
) -> None:
    result = exercise_call(summarize_pairs, xs, ys)
    assert result.count == 2
    assert result.covariance == 0.0
    assert result.correlation is None


def test_negative_relation_and_inputs_unchanged() -> None:
    xs, ys = [1.0, 2.0, 3.0], [6.0, 4.0, 2.0]
    result = exercise_call(summarize_pairs, xs, ys)
    assert result.count == 3
    assert result.mean_x == pytest.approx(2.0)
    assert result.mean_y == pytest.approx(4.0)
    assert result.covariance == pytest.approx(-2.0)
    assert result.correlation == pytest.approx(-1.0)
    assert xs == [1.0, 2.0, 3.0]
    assert ys == [6.0, 4.0, 2.0]


@pytest.mark.parametrize(("xs", "ys"), [([1.0], []), ([], [1.0]), ([1.0, 2.0], [1.0])])
def test_unequal_lengths_are_not_silently_truncated(xs: list[float], ys: list[float]) -> None:
    with pytest.raises(ValueError, match="length"):
        exercise_call(summarize_pairs, xs, ys)
