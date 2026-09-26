"""Exact scores expose rank origin, accumulation and tie-policy mistakes."""

import pytest

from roadmap_tools import exercise_call

from .starter import fuse_rankings


def test_weighted_consensus_uses_one_based_ranks() -> None:
    hits = exercise_call(
        fuse_rankings, [["a", "b"], ["b", "c"]], weights=[1.0, 0.5], rank_constant=1.0
    )
    assert [hit.document_id for hit in hits] == ["b", "a", "c"]
    assert [hit.score for hit in hits] == pytest.approx([1 / 3 + 1 / 4, 1 / 2, 1 / 6])


def test_ties_are_lexicographic_and_default_weights_are_one() -> None:
    hits = exercise_call(fuse_rankings, [["z"], ["a"]], rank_constant=2.0, top_k=1)
    assert len(hits) == 1
    assert hits[0].document_id == "a"
    assert hits[0].score == pytest.approx(1 / 3)


def test_zero_weight_branch_adds_neither_candidates_nor_scores() -> None:
    hits = exercise_call(fuse_rankings, [["hidden-by-config", "a"], ["b"]], weights=[0.0, 1.0])
    assert [hit.document_id for hit in hits] == ["b"]
    assert hits[0].score == pytest.approx(1 / 61)
    assert exercise_call(fuse_rankings, [["a"]], weights=[0.0]) == ()


def test_empty_inputs_large_limit_and_input_preservation() -> None:
    rankings = [["a", "b"], []]
    weights = [1.0, 0.5]
    hits = exercise_call(fuse_rankings, rankings, weights=weights, top_k=50)
    assert [hit.document_id for hit in hits] == ["a", "b"]
    assert rankings == [["a", "b"], []]
    assert weights == [1.0, 0.5]
    assert exercise_call(fuse_rankings, []) == ()
    assert exercise_call(fuse_rankings, [[], []]) == ()
    assert exercise_call(fuse_rankings, rankings, top_k=0) == ()


@pytest.mark.parametrize("rankings", [[["a", "a"]], [[""]], [["   "]]])
def test_bad_ids_rejected_even_in_disabled_branch(rankings: list[list[str]]) -> None:
    with pytest.raises(ValueError, match="document"):
        exercise_call(fuse_rankings, rankings, weights=[0.0], top_k=0)


@pytest.mark.parametrize("weights", [[], [1.0, 1.0], [-0.1], [1.1], [float("nan")], [float("inf")]])
def test_invalid_weights_rejected(weights: list[float]) -> None:
    with pytest.raises(ValueError, match="weight"):
        exercise_call(fuse_rankings, [["a"]], weights=weights)


@pytest.mark.parametrize("rank_constant", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_constant_rejected(rank_constant: float) -> None:
    with pytest.raises(ValueError, match="rank_constant"):
        exercise_call(fuse_rankings, [], rank_constant=rank_constant)


@pytest.mark.parametrize("top_k", [-1, True])
def test_invalid_limit_rejected(top_k: int) -> None:
    with pytest.raises(ValueError, match="top_k"):
        exercise_call(fuse_rankings, [], top_k=top_k)
