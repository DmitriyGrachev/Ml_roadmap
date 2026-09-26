"""Student boundary for deciding from complete canary measurement windows."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Window:
    requests: int
    failures: int
    p95_ms: float | None


@dataclass(frozen=True)
class RolloutPolicy:
    min_requests: int = 100
    max_error_rate: float = 0.01
    max_p95_ms: float = 500.0
    promote_after: int = 3
    rollback_after: int = 2


@dataclass(frozen=True)
class RolloutDecision:
    action: Literal["hold", "promote", "rollback"]
    processed_windows: int
    healthy_streak: int
    unhealthy_streak: int
    reason: str


def decide_rollout(windows: Sequence[Window], policy: RolloutPolicy) -> RolloutDecision:
    """Validate all observations, then apply the README's consecutive-window policy."""
    # TODO: validate the whole input and find the first terminal decision, or hold.
    raise NotImplementedError("decide bounded canary rollout")
