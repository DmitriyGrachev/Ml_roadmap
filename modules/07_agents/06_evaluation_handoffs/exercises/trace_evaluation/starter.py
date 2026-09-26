"""Measure policy compliance and efficiency alongside final-answer correctness."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolEvent:
    tool: str
    arguments_key: str
    authorized: bool
    succeeded: bool


@dataclass(frozen=True)
class Trace:
    run_id: str
    final_correct: bool
    steps: int
    max_steps: int
    max_tool_calls: int
    calls: tuple[ToolEvent, ...]


@dataclass(frozen=True)
class TraceMetrics:
    runs: int
    successful_runs: int
    success_rate: float
    policy_violations: int
    limit_violations: int
    redundant_calls: int
    total_tool_calls: int
    tool_failure_rate: float | None


def evaluate_traces(traces: tuple[Trace, ...]) -> TraceMetrics:
    """Validate and score the exact per-run and per-call rules in README.md."""
    raise NotImplementedError("Implement workflow trace evaluation")
