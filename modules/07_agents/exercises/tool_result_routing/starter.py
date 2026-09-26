"""Compute a next action without executing a tool, retry, or handoff."""

from dataclasses import dataclass
from typing import Literal

type ToolStatus = Literal["success", "transient", "permanent", "permission-denied"]
type RouteReason = Literal[
    "success",
    "transient",
    "permanent",
    "permission-denied",
    "attempts-exhausted",
    "budget-exhausted",
]


@dataclass(frozen=True)
class ToolResult:
    status: ToolStatus
    payload: str


@dataclass(frozen=True)
class Route:
    action: Literal["finish", "retry", "handoff"]
    reason: RouteReason
    output: str | None


def route_result(
    result: ToolResult, attempts: int, max_attempts: int, remaining_calls: int
) -> Route:
    """Validate counters and route a completed attempt using the README precedence."""
    # TODO: Separate successful output, retryable failures, and terminal handoffs.
    raise NotImplementedError("Implement bounded tool-result routing")
