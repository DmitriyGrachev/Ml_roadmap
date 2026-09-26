"""Test deterministic streak policies; nothing is deployed or rolled back."""

from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import RolloutDecision, RolloutPolicy, Window, decide_rollout


def test_threshold_equality_promotes_after_three_consecutive_good_windows() -> None:
    windows = [Window(100, 1, 500.0)] * 3 + [Window(100, 50, 1000.0)]
    assert exercise_call(decide_rollout, windows, RolloutPolicy()) == RolloutDecision(
        "promote",
        3,
        3,
        0,
        "healthy-streak",
    )


def test_error_or_latency_regression_causes_rollback_after_two_windows() -> None:
    windows = [Window(100, 2, 100.0), Window(100, 0, 501.0), Window(100, 0, 1.0)]
    assert exercise_call(decide_rollout, windows, RolloutPolicy()) == RolloutDecision(
        "rollback",
        2,
        0,
        2,
        "unhealthy-streak",
    )


def test_insufficient_data_resets_both_streaks_and_cannot_imply_success() -> None:
    windows = [Window(100, 0, 10.0), Window(0, 0, None), Window(100, 0, 10.0)]
    assert exercise_call(decide_rollout, windows, RolloutPolicy()) == RolloutDecision(
        "hold",
        3,
        1,
        0,
        "warming-up",
    )
    assert exercise_call(
        decide_rollout, [Window(99, 90, 1000.0)], RolloutPolicy()
    ) == RolloutDecision(
        "hold",
        1,
        0,
        0,
        "insufficient-data",
    )


def test_alternating_health_resets_streaks_and_empty_input_is_explicit() -> None:
    windows = [Window(100, 0, 1.0), Window(100, 2, 1.0), Window(100, 0, 1.0), Window(100, 2, 1.0)]
    assert exercise_call(decide_rollout, windows, RolloutPolicy()) == RolloutDecision(
        "hold",
        4,
        0,
        1,
        "watching-regression",
    )
    assert exercise_call(decide_rollout, [], RolloutPolicy()) == RolloutDecision(
        "hold", 0, 0, 0, "no-data"
    )


def test_policy_can_require_a_single_window_and_input_remains_unchanged() -> None:
    windows = [Window(5, 0, 0.0)]
    before = windows.copy()
    policy = RolloutPolicy(min_requests=5, promote_after=1)
    first = exercise_call(decide_rollout, windows, policy)
    assert first == exercise_call(decide_rollout, windows, policy)
    assert first.action == "promote"
    assert first.processed_windows == 1
    assert windows == before


@pytest.mark.parametrize(
    "window",
    [
        Window(-1, 0, None),
        Window(1, -1, 1.0),
        Window(1, 2, 1.0),
        Window(0, 0, 1.0),
        Window(1, 0, None),
        Window(1, 0, -1.0),
        Window(1, 0, float("nan")),
        Window(1, 0, float("inf")),
        Window(cast(int, True), 0, 1.0),
        Window(1, cast(int, True), 1.0),
        Window(1, 0, cast(float, True)),
    ],
)
def test_invalid_windows_including_after_an_early_terminal_decision(window: Window) -> None:
    with pytest.raises(ValueError, match=r"window|requests|failures|p95"):
        exercise_call(decide_rollout, [Window(100, 0, 1.0)] * 3 + [window], RolloutPolicy())


@pytest.mark.parametrize(
    "policy",
    [
        RolloutPolicy(min_requests=0),
        RolloutPolicy(min_requests=True),
        RolloutPolicy(promote_after=0),
        RolloutPolicy(rollback_after=-1),
        RolloutPolicy(promote_after=cast(int, 1.5)),
        RolloutPolicy(max_error_rate=-0.1),
        RolloutPolicy(max_error_rate=1.1),
        RolloutPolicy(max_error_rate=float("nan")),
        RolloutPolicy(max_p95_ms=0),
        RolloutPolicy(max_p95_ms=float("inf")),
    ],
)
def test_invalid_policy_is_rejected_even_without_windows(policy: RolloutPolicy) -> None:
    with pytest.raises(ValueError, match=r"policy|min_requests|promote|rollback|error_rate|p95"):
        exercise_call(decide_rollout, [], policy)
