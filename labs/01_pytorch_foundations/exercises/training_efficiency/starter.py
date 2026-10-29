"""Learner-owned logical-batch update; caller owns model mode and optimizer."""

from collections.abc import Callable, Sequence
from typing import Any


def accumulated_step(
    model: Any,
    optimizer: Any,
    batches: Sequence[tuple[Any, Any]],
    loss_fn: Callable[..., Any],
) -> float:
    """One update equivalent to concatenation; loss_fn returns a mean over rows.

    Reject empty input/empty micro-batches before updating. Clear old gradients,
    weight each micro-batch loss by its row fraction, backward each, step once.
    Return the detached logical-batch mean loss; retain final accumulated grads.
    """
    raise NotImplementedError("Implement row-weighted gradient accumulation")
