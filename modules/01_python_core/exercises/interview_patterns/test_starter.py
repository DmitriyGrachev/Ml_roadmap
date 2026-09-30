"""Behavioral interview variations; unfinished learner calls are xfailed."""

from collections.abc import Mapping, Sequence

import pytest

from roadmap_tools.exercise import exercise_call

from .instrumentation import ComparisonSequence, OneShotValues
from .starter import lower_bound, reachable, top_k

pytestmark = pytest.mark.student_exercise


@pytest.mark.parametrize(
    ("values", "target", "expected"),
    [
        ([], 3, 0),
        ([2], 1, 0),
        ([2], 3, 1),
        ([1, 2, 2, 2, 5], 2, 1),
        ([1, 2, 2, 2, 5], 4, 4),
        ([1, 2, 2, 2, 5], 9, 5),
    ],
)
def test_lower_bound_returns_first_valid_insertion_position(
    values: list[int], target: int, expected: int
) -> None:
    assert exercise_call(lower_bound, values, target) == expected


def test_lower_bound_uses_logarithmically_many_value_comparisons() -> None:
    values = ComparisonSequence(range(0, 2048, 2))
    assert exercise_call(lower_bound, values, 999) == 500
    assert values.comparisons <= 44


@pytest.mark.parametrize(
    ("values", "k", "expected"),
    [
        ([], 0, ()),
        ([], 3, ()),
        ([4, 1, 4, 2], 0, ()),
        ([4, 1, 4, 2], 2, (4, 4)),
        ([4, 1, 4, 2], 8, (4, 4, 2, 1)),
    ],
)
def test_top_k_preserves_duplicates_in_descending_order(
    values: list[int], k: int, expected: tuple[int, ...]
) -> None:
    assert exercise_call(top_k, values, k) == expected


def test_top_k_consumes_a_one_shot_source_once() -> None:
    values = OneShotValues([3, 9, 3, 7, 1])
    assert exercise_call(top_k, values, 3) == (9, 7, 3)
    assert values.iterations == 1
    assert values.pulls == 5


def test_top_k_rejects_negative_k() -> None:
    with pytest.raises(ValueError, match="k"):
        exercise_call(top_k, [1, 2], -1)


@pytest.mark.parametrize(
    ("traversal", "expected"),
    [
        ("bfs", ("a", "b", "c", "d", "e")),
        ("dfs", ("a", "b", "d", "c", "e")),
    ],
)
def test_reachable_respects_neighbor_order_and_skips_cycles(
    traversal: str, expected: tuple[str, ...]
) -> None:
    graph: Mapping[str, Sequence[str]] = {
        "a": ("b", "c"),
        "b": ("d",),
        "c": ("d", "e"),
        "d": ("a",),
        "e": (),
        "detached": (),
    }
    assert exercise_call(reachable, graph, "a", traversal=traversal) == expected


def test_reachable_is_singleton_for_isolated_start() -> None:
    assert exercise_call(reachable, {"alone": (), "other": ()}, "alone", traversal="bfs") == (
        "alone",
    )


def test_reachable_rejects_unknown_start() -> None:
    with pytest.raises(ValueError, match="start"):
        exercise_call(reachable, {}, "absent", traversal="dfs")
