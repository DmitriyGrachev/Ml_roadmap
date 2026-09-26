"""Aggregate complete measurement windows with explicit no-data behavior."""

# ruff: noqa: PT011 -- The public contract specifies exception classes, not message text.

from decimal import Decimal, localcontext
from typing import cast

import pytest

from roadmap_tools import exercise_call

from .starter import BudgetSummary, MeasurementWindow, NoDataPolicy, summarize_error_budget


def test_uses_request_weighted_totals_and_allows_exact_budget() -> None:
    windows = (MeasurementWindow("busy", 900, 8, True), MeasurementWindow("quiet", 100, 2, True))
    assert exercise_call(summarize_error_budget, windows, Decimal("0.99"), "block") == (
        BudgetSummary(2, 1000, 10, 10, 0, True)
    )
    assert windows == (
        MeasurementWindow("busy", 900, 8, True),
        MeasurementWindow("quiet", 100, 2, True),
    )


def test_rounds_allowed_failures_down_and_preserves_negative_remainder() -> None:
    assert exercise_call(
        summarize_error_budget, (MeasurementWindow("a", 99, 1, True),), Decimal("0.99"), "allow"
    ) == BudgetSummary(1, 99, 1, 0, -1, False)


def test_incomplete_window_does_not_consume_or_expand_budget() -> None:
    windows = (
        MeasurementWindow("complete", 100, 1, True),
        MeasurementWindow("partial", 1000, 500, False),
    )
    assert exercise_call(summarize_error_budget, windows, Decimal("0.99"), "block") == (
        BudgetSummary(1, 100, 1, 1, 0, True)
    )


@pytest.mark.parametrize(("policy", "allowed"), [("allow", True), ("block", False)])
def test_empty_input_uses_no_data_policy(policy: NoDataPolicy, allowed: bool) -> None:
    assert exercise_call(summarize_error_budget, (), Decimal("0.99"), policy) == (
        BudgetSummary(0, 0, 0, 0, 0, allowed)
    )


def test_complete_zero_traffic_window_counts_but_still_has_no_data() -> None:
    assert exercise_call(
        summarize_error_budget, (MeasurementWindow("empty", 0, 0, True),), Decimal("1"), "block"
    ) == BudgetSummary(1, 0, 0, 0, 0, False)


@pytest.mark.parametrize(
    ("target", "allowed", "remaining", "permitted"),
    [
        (Decimal("0"), 3, 1, True),
        (Decimal("1"), 0, -2, False),
    ],
)
def test_target_endpoints_have_exact_meaning(
    target: Decimal, allowed: int, remaining: int, permitted: bool
) -> None:
    assert exercise_call(
        summarize_error_budget, (MeasurementWindow("a", 3, 2, True),), target, "block"
    ) == BudgetSummary(1, 3, 2, allowed, remaining, permitted)


@pytest.mark.parametrize(
    "target", [Decimal("NaN"), Decimal("Infinity"), Decimal("-0.1"), Decimal("1.1")]
)
def test_rejects_nonfinite_or_out_of_range_target(target: Decimal) -> None:
    with pytest.raises(ValueError):
        exercise_call(summarize_error_budget, (), target, "block")


@pytest.mark.parametrize(
    "window",
    [
        MeasurementWindow("a", -1, 0, False),
        MeasurementWindow("a", 1, 2, False),
        MeasurementWindow("a", 1, -1, False),
        MeasurementWindow("a", True, 0, False),
        MeasurementWindow("a", 1, True, False),
        MeasurementWindow("", 1, 0, True),
        MeasurementWindow(" a", 1, 0, True),
        MeasurementWindow("a", 1, 0, cast(bool, 1)),
    ],
)
def test_validates_even_incomplete_windows(window: MeasurementWindow) -> None:
    with pytest.raises(ValueError):
        exercise_call(summarize_error_budget, (window,), Decimal("0.99"), "allow")


def test_duplicate_window_ids_cannot_double_count_measurements() -> None:
    with pytest.raises(ValueError):
        exercise_call(
            summarize_error_budget,
            (MeasurementWindow("a", 10, 0, True), MeasurementWindow("a", 20, 0, False)),
            Decimal("0.99"),
            "block",
        )


def test_unknown_no_data_policy_is_rejected_even_with_traffic() -> None:
    with pytest.raises(ValueError):
        exercise_call(
            summarize_error_budget,
            (MeasurementWindow("a", 10, 0, True),),
            Decimal("0.99"),
            cast(NoDataPolicy, "ignore"),
        )


def test_allowance_is_exact_even_under_low_decimal_precision() -> None:
    with localcontext() as context:
        context.prec = 3
        result = exercise_call(
            summarize_error_budget,
            (MeasurementWindow("a", 123456, 0, True),),
            Decimal("0.99"),
            "block",
        )
    assert result == BudgetSummary(1, 123456, 0, 1234, 1234, True)


def test_only_incomplete_windows_use_no_data_policy() -> None:
    assert exercise_call(
        summarize_error_budget,
        (MeasurementWindow("partial", 500, 0, False),),
        Decimal("0.99"),
        "block",
    ) == BudgetSummary(0, 0, 0, 0, 0, False)
