"""A finite loop over typed proposals and one application-selected read tool."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class CallTool:
    exhibit_id: str


@dataclass(frozen=True)
class Finish:
    answer: str


@dataclass(frozen=True)
class Observation:
    exhibit_id: str
    text: str


@dataclass(frozen=True)
class TraceEvent:
    step: int
    kind: Literal["proposal", "tool_result", "finish", "limit", "error"]
    detail: str


@dataclass(frozen=True)
class RunResult:
    status: Literal["finished", "step_limit", "tool_limit", "tool_error"]
    answer: str | None
    model_steps: int
    tool_calls: int
    observations: tuple[Observation, ...]
    trace: tuple[TraceEvent, ...]


class Model(Protocol):
    def propose(self, observations: tuple[Observation, ...]) -> CallTool | Finish:
        """Return a typed proposal without authority to execute tools."""
        ...


class ToolFailure(RuntimeError):
    """A classified failure of the application-selected tool."""


def run_agent(
    model: Model,
    tool: Callable[[str], str],
    max_steps: int,
    max_tool_calls: int,
) -> RunResult:
    """Run the finite state machine and exact audit contract in README.md."""
    raise NotImplementedError("Implement the bounded exhibit assistant")
