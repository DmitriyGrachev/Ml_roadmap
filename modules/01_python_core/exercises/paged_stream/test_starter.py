"""Observe pull counts at consumer boundaries, without timing assumptions."""

from collections.abc import Iterator
from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import iter_pages

pytestmark = pytest.mark.student_exercise


def collect(source: Iterator[int], size: int) -> list[tuple[int, ...]]:
    return list(iter_pages(source, size))


@pytest.mark.parametrize(
    ("values", "size", "expected"),
    [
        ([], 2, []),
        ([1], 3, [(1,)]),
        ([1, 2, 3, 4], 2, [(1, 2), (3, 4)]),
        ([1, 2, 3], 2, [(1, 2), (3,)]),
        ([2, 2], 1, [(2,), (2,)]),
    ],
)
def test_page_boundaries(values: list[int], size: int, expected: list[tuple[int, ...]]) -> None:
    assert exercise_call(collect, iter(values), size) == expected


def test_does_not_read_ahead_and_leaves_unrequested_values_available() -> None:
    pulled: list[int] = []

    def source() -> Iterator[int]:
        for value in range(5):
            pulled.append(value)
            yield value

    stream = source()
    pages = exercise_call(iter_pages, stream, 2)
    assert pulled == []
    assert exercise_call(next, pages) == (0, 1)
    assert pulled == [0, 1]
    assert next(stream) == 2
    assert exercise_call(next, pages) == (3, 4)
    assert exercise_call(list, pages) == []


def test_supports_non_numeric_items_without_mutation() -> None:
    values = ["oak", "elm", "ash"]
    pages = exercise_call(iter_pages, values, 2)
    assert exercise_call(list, pages) == [("oak", "elm"), ("ash",)]
    assert values == ["oak", "elm", "ash"]


def test_source_exception_is_not_swallowed() -> None:
    def source() -> Iterator[int]:
        yield 1
        raise RuntimeError("sensor disconnected")

    pages = exercise_call(iter_pages, source(), 1)
    assert exercise_call(next, pages) == (1,)
    with pytest.raises(RuntimeError, match="sensor disconnected"):
        exercise_call(next, pages)


def test_source_error_during_a_partial_page_is_propagated_without_yield() -> None:
    def source() -> Iterator[int]:
        yield 1
        raise RuntimeError("sensor disconnected")

    pages = exercise_call(iter_pages, source(), 2)
    with pytest.raises(RuntimeError, match="sensor disconnected"):
        exercise_call(next, pages)


@pytest.mark.parametrize("size", [0, -1, True, 1.5])
def test_invalid_size_does_not_consume_source(size: object) -> None:
    source = iter([10, 20])
    with pytest.raises(ValueError, match="size"):
        exercise_call(collect, source, cast(int, size))
    assert next(source) == 10
