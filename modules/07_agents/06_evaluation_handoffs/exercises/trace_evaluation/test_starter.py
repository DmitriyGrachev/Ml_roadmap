"""A correct final answer must not erase unauthorized execution or budget overruns."""

from dataclasses import replace

import pytest

from roadmap_tools import exercise_call

from .starter import ToolEvent, Trace, TraceMetrics, evaluate_traces


def test_reports_success_policy_efficiency_and_failed_tool_calls() -> None:
    lookup = ToolEvent("lookup", "book=A", True, True)
    traces = (
        Trace("good", True, 2, 3, 2, (lookup,)),
        Trace("denied", True, 2, 3, 2, (ToolEvent("reserve", "room=A", False, True),)),
        Trace("over", True, 4, 3, 1, (lookup, lookup)),
        Trace("wrong", False, 1, 3, 2, (ToolEvent("lookup", "book=B", True, False),)),
    )
    result = exercise_call(evaluate_traces, traces)
    assert result == TraceMetrics(4, 1, 0.25, 1, 1, 1, 5, 0.2)


def test_redundancy_is_per_run_and_counts_each_repeat_after_first() -> None:
    same = ToolEvent("lookup", "book=A", True, True)
    other_args = ToolEvent("lookup", "book=B", True, True)
    other_tool = ToolEvent("describe", "book=A", True, True)
    result = exercise_call(
        evaluate_traces,
        (
            Trace("a", True, 6, 6, 6, (same, other_args, same, other_tool, same)),
            Trace("b", True, 1, 2, 2, (same,)),
        ),
    )
    assert result.redundant_calls == 2
    assert result.successful_runs == 2


def test_no_calls_has_undefined_tool_failure_rate_and_valid_success() -> None:
    assert exercise_call(evaluate_traces, (Trace("a", True, 1, 1, 0, ()),)) == TraceMetrics(
        1, 1, 1.0, 0, 0, 0, 0, None
    )


def test_exact_limits_are_allowed_and_recovered_tool_failure_does_not_prevent_success() -> None:
    result = exercise_call(
        evaluate_traces,
        (Trace("a", True, 2, 2, 1, (ToolEvent("lookup", "A", True, False),)),),
    )
    assert result.successful_runs == 1
    assert result.limit_violations == 0
    assert result.tool_failure_rate == 1.0


def test_multiple_unauthorized_calls_count_individually_and_both_limits_count_once() -> None:
    calls = (ToolEvent("lookup", "A", False, False), ToolEvent("lookup", "B", False, True))
    result = exercise_call(evaluate_traces, (Trace("a", True, 3, 1, 1, calls),))
    assert result.policy_violations == 2
    assert result.limit_violations == 1
    assert result.successful_runs == 0


@pytest.mark.parametrize(
    "trace",
    [
        Trace("steps-only", True, 2, 1, 0, ()),
        Trace("calls-only", True, 1, 1, 0, (ToolEvent("lookup", "A", True, True),)),
    ],
    ids=["steps-only", "calls-only"],
)
def test_either_limit_alone_disqualifies_success(trace: Trace) -> None:
    result = exercise_call(evaluate_traces, (trace,))
    assert result.limit_violations == 1
    assert result.successful_runs == 0
    assert result.success_rate == 0.0
    assert result.policy_violations == 0


@pytest.mark.parametrize(
    "traces",
    [(), (Trace(" ", True, 0, 1, 0, ()),), (Trace("a", True, 0, 1, 0, ()),) * 2],
)
def test_requires_nonempty_traces_and_unique_nonblank_run_ids(traces: tuple[Trace, ...]) -> None:
    with pytest.raises(ValueError, match=r"trace|run"):
        exercise_call(evaluate_traces, traces)


@pytest.mark.parametrize(
    "trace",
    [
        Trace("a", True, -1, 1, 0, ()),
        Trace("a", True, 1, 0, 0, ()),
        Trace("a", True, 1, 1, -1, ()),
        Trace("a", True, True, 1, 0, ()),
    ],
)
def test_rejects_invalid_counter_metadata(trace: Trace) -> None:
    with pytest.raises(ValueError, match=r"steps|tool"):
        exercise_call(evaluate_traces, (trace,))


@pytest.mark.parametrize(
    "event", [ToolEvent(" ", "A", True, True), ToolEvent("lookup", "", True, True)]
)
def test_requires_tool_name_and_application_argument_key(event: ToolEvent) -> None:
    with pytest.raises(ValueError, match=r"tool|argument"):
        exercise_call(evaluate_traces, (Trace("a", True, 1, 1, 1, (event,)),))


def test_input_records_remain_unchanged() -> None:
    trace = Trace("a", True, 1, 1, 1, (ToolEvent("lookup", "A", True, True),))
    before = replace(trace)
    exercise_call(evaluate_traces, (trace,))
    assert trace == before
