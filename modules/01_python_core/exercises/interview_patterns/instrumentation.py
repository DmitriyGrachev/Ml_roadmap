"""Observable inputs for complexity and one-pass assertions, without solutions."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import overload


class _ComparisonValue(int):
    _owner: ComparisonSequence

    def __new__(cls, value: int, owner: ComparisonSequence) -> _ComparisonValue:
        instance = int.__new__(cls, value)
        instance._owner = owner
        return instance

    def __lt__(self, other: int) -> bool:
        self._owner.comparisons += 1
        return int(self) < other

    def __le__(self, other: int) -> bool:
        self._owner.comparisons += 1
        return int(self) <= other

    def __gt__(self, other: int) -> bool:
        self._owner.comparisons += 1
        return int(self) > other

    def __ge__(self, other: int) -> bool:
        self._owner.comparisons += 1
        return int(self) >= other

    def __eq__(self, other: object) -> bool:
        self._owner.comparisons += 1
        return int(self) == other

    def __ne__(self, other: object) -> bool:
        self._owner.comparisons += 1
        return int(self) != other

    __hash__ = int.__hash__


class ComparisonSequence(Sequence[int]):
    """Return counted int values from a finite, read-only sequence."""

    def __init__(self, values: Iterable[int]) -> None:
        self._values = tuple(values)
        self.comparisons = 0

    def __len__(self) -> int:
        return len(self._values)

    @overload
    def __getitem__(self, index: int) -> int: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[int]: ...

    def __getitem__(self, index: int | slice) -> int | Sequence[int]:
        if isinstance(index, slice):
            return tuple(_ComparisonValue(value, self) for value in self._values[index])
        return _ComparisonValue(self._values[index], self)


class OneShotValues(Iterable[int]):
    """Reject a second pass and count items actually yielded."""

    def __init__(self, values: Iterable[int]) -> None:
        self._values = tuple(values)
        self.iterations = 0
        self.pulls = 0

    def __iter__(self) -> Iterator[int]:
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError("input was iterated more than once")
        for value in self._values:
            self.pulls += 1
            yield value
