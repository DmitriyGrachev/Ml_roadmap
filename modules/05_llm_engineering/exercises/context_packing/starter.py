"""Student boundary for stable priority-based context packing."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextSegment:
    """A supplied segment with an already measured token cost."""

    id: str
    text: str
    tokens: int
    priority: int


@dataclass(frozen=True)
class PackedContext:
    """Selected segments in their original order and their token total."""

    segments: tuple[ContextSegment, ...]
    used_tokens: int


def pack_context(
    segments: tuple[ContextSegment, ...],
    *,
    budget: int,
    reserved: int = 0,
) -> PackedContext:
    """Greedily pack available capacity according to the README."""
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    if type(reserved) is not int or not 0 <= reserved <= budget:
        raise ValueError("reserved must be an integer between zero and budget")
    ids: set[str] = set()
    for segment in segments:
        if not isinstance(segment.id, str) or not segment.id.strip() or segment.id in ids:
            raise ValueError("segment IDs must be unique nonblank strings")
        if not isinstance(segment.text, str):
            raise ValueError("segment text must be a string")
        if type(segment.tokens) is not int or segment.tokens <= 0:
            raise ValueError("segment tokens must be a positive integer")
        if type(segment.priority) is not int:
            raise ValueError("segment priority must be an integer")
        ids.add(segment.id)
    # TODO: visit by stable priority, select fitting segments, restore source order.
    raise NotImplementedError("priority-aware context packing")
