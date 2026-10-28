"""Student boundary: audit frozen binary decisions by declared technical group."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GroupSlice:
    group: str
    support: int
    tp: int
    fp: int
    fn: int
    tn: int
    selection_rate: float | None
    tpr: float | None
    fpr: float | None
    precision: float | None


def grouped_slices(
    actual: tuple[int, ...],
    decisions: tuple[int, ...],
    memberships: tuple[str, ...],
    *,
    groups: tuple[str, ...],
) -> tuple[GroupSlice, ...]:
    """Return every declared group in caller order, including absent groups."""
    if not (len(actual) == len(decisions) == len(memberships)):
        raise ValueError("lengths must match")
    if not groups or any(not isinstance(group, str) or not group.strip() for group in groups):
        raise ValueError("groups must be nonblank strings")
    if len(set(groups)) != len(groups):
        raise ValueError("groups must be unique")
    if any(group not in groups for group in memberships):
        raise ValueError("unknown membership")
    if any(type(label) is not int or label not in (0, 1) for label in (*actual, *decisions)):
        raise ValueError("labels must be exact integers zero or one")
    # TODO: count each group's cells and derive rates, preserving undefined as None.
    raise NotImplementedError("grouped sensor slices")
