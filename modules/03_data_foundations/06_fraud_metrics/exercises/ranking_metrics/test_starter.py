"""Acceptance tests for the fraud ranking-metric student boundaries."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

import pytest

from roadmap_tools import exercise_call

from .starter import pr_auc, roc_auc

MetricFunction = Callable[[Sequence[int], Sequence[float]], float]


def test_roc_auc_matches_a_known_pairwise_ranking() -> None:
    result = exercise_call(
        roc_auc,
        labels=[0, 0, 1, 1],
        scores=[0.1, 0.4, 0.35, 0.8],
    )

    assert result == pytest.approx(0.75)


def test_roc_auc_gives_half_credit_to_tied_positive_negative_pairs() -> None:
    result = exercise_call(
        roc_auc,
        labels=[1, 0, 1, 0],
        scores=[0.9, 0.9, 0.2, 0.1],
    )

    assert result == pytest.approx(0.625)


def test_pr_auc_matches_the_documented_trapezoidal_curve() -> None:
    result = exercise_call(
        pr_auc,
        labels=[1, 0, 1],
        scores=[0.9, 0.8, 0.7],
    )

    assert result == pytest.approx(0.7916666666666666)


def test_pr_auc_consumes_tied_scores_as_one_threshold_group() -> None:
    result = exercise_call(
        pr_auc,
        labels=[1, 0, 1, 0],
        scores=[0.9, 0.9, 0.2, 0.1],
    )

    assert result == pytest.approx(0.6666666666666666)


@pytest.mark.parametrize("metric", [roc_auc, pr_auc], ids=["roc", "pr"])
def test_metric_is_invariant_to_paired_input_order(metric: MetricFunction) -> None:
    forward = exercise_call(metric, [1, 0, 1, 0], [0.9, 0.9, 0.2, 0.1])
    reversed_order = exercise_call(metric, [0, 1, 0, 1], [0.1, 0.2, 0.9, 0.9])

    assert forward == pytest.approx(reversed_order)


@pytest.mark.parametrize("metric", [roc_auc, pr_auc], ids=["roc", "pr"])
def test_rejects_empty_input(metric: MetricFunction) -> None:
    with pytest.raises(ValueError, match=r"empty|label"):
        exercise_call(metric, [], [])


@pytest.mark.parametrize("metric", [roc_auc, pr_auc], ids=["roc", "pr"])
def test_rejects_length_mismatch(metric: MetricFunction) -> None:
    with pytest.raises(ValueError, match="length"):
        exercise_call(metric, [0, 1], [0.2])


@pytest.mark.parametrize("metric", [roc_auc, pr_auc], ids=["roc", "pr"])
def test_rejects_non_binary_labels(metric: MetricFunction) -> None:
    with pytest.raises(ValueError, match=r"binary|0|1"):
        exercise_call(metric, [0, 2], [0.2, 0.8])


@pytest.mark.parametrize("metric", [roc_auc, pr_auc], ids=["roc", "pr"])
@pytest.mark.parametrize("invalid_score", [-0.01, 1.01, math.nan, math.inf, -math.inf])
def test_rejects_invalid_scores(metric: MetricFunction, invalid_score: float) -> None:
    with pytest.raises(ValueError, match=r"score|finite|\[0, 1\]"):
        exercise_call(metric, [0, 1], [0.2, invalid_score])


@pytest.mark.parametrize("metric", [roc_auc, pr_auc], ids=["roc", "pr"])
@pytest.mark.parametrize("labels", [[0, 0], [1, 1]], ids=["negative-only", "positive-only"])
def test_rejects_single_class_labels(metric: MetricFunction, labels: list[int]) -> None:
    with pytest.raises(ValueError, match=r"class|positive|negative"):
        exercise_call(metric, labels, [0.2, 0.8])
