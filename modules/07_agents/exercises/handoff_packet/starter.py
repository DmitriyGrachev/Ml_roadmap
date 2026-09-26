"""Transfer explicitly permitted facts with required metadata and a character budget."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HandoffFact:
    name: str
    value: str
    capability: str


@dataclass(frozen=True)
class VisibleFact:
    name: str
    value: str


@dataclass(frozen=True)
class HandoffPacket:
    case_id: str
    reason: str
    facts: tuple[VisibleFact, ...]
    truncated: bool


def build_handoff(
    case_id: str,
    reason: str,
    facts: tuple[HandoffFact, ...],
    recipient_capabilities: frozenset[str],
    max_chars: int,
) -> HandoffPacket:
    """Validate all facts, filter by permission, then apply the documented budget."""
    # TODO: Preserve required metadata and deterministically bound permitted content.
    raise NotImplementedError("Implement permission-filtered library handoff")
