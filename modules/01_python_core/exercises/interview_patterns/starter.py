"""Student-owned Python interview variations."""

from collections.abc import Iterable, Mapping, Sequence
from typing import Literal


def lower_bound(values: Sequence[int], target: int) -> int:
    """Return the first insertion index for target in sorted values."""
    raise NotImplementedError("Implement lower_bound")


def top_k(values: Iterable[int], k: int) -> tuple[int, ...]:
    """Return up to k greatest values in descending order, keeping duplicates."""
    raise NotImplementedError("Implement top_k")


def reachable(
    graph: Mapping[str, Sequence[str]],
    start: str,
    *,
    traversal: Literal["bfs", "dfs"],
) -> tuple[str, ...]:
    """Visit reachable vertices in deterministic neighbor order."""
    raise NotImplementedError("Implement reachable")
