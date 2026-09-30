"""Learner-owned training-state boundaries."""

from collections.abc import Mapping
from dataclasses import dataclass

from torch import nn
from torch.optim import Optimizer


@dataclass(frozen=True)
class TrainingCursor:
    """Position immediately after an optimizer step; exhausted order stays until next step."""

    epoch: int
    global_step: int
    sample_order: tuple[str, ...]
    next_batch_offset: int


def capture_state(
    model: nn.Module,
    optimizer: Optimizer,
    cursor: TrainingCursor,
    identity: Mapping[str, str],
) -> dict[str, object]:
    """Capture independent model/optimizer, primitive cursor/identity, and all used RNG states."""
    raise NotImplementedError("Capture state after the completed optimizer step")


def restore_state(
    model: nn.Module,
    optimizer: Optimizer,
    state: Mapping[str, object],
    identity: Mapping[str, str],
) -> TrainingCursor:
    """Validate compatibility, restore all state, and return the exact next-batch cursor."""
    raise NotImplementedError("Validate identity/cursor and restore the same training trajectory")
