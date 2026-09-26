"""Hand-checked paired release cases, including hidden slice regressions."""

from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import CaseResult, GateReport, SliceComparison, evaluate_release


def test_slice_regression_cannot_be_hidden_by_equal_overall_accuracy() -> None:
    baseline = [
        CaseResult("a", "refusal", True),
        CaseResult("b", "refusal", True),
        CaseResult("c", "facts", False),
        CaseResult("d", "facts", False),
    ]
    candidate = [
        CaseResult("d", "facts", True),
        CaseResult("b", "refusal", False),
        CaseResult("a", "refusal", True),
        CaseResult("c", "facts", False),
    ]
    assert exercise_call(evaluate_release, baseline, candidate) == GateReport(
        False,
        (SliceComparison("facts", 2, 0.0, 0.5), SliceComparison("refusal", 2, 1.0, 0.5)),
        ("refusal:regression",),
    )


def test_regression_at_allowed_boundary_passes_without_rounding() -> None:
    baseline = [CaseResult("a", "facts", True), CaseResult("b", "facts", True)]
    candidate = [CaseResult("a", "facts", False), CaseResult("b", "facts", True)]
    assert exercise_call(evaluate_release, baseline, candidate, max_regression=0.5).accepted


def test_decimal_fraction_regression_uses_the_documented_float_allowance() -> None:
    baseline = [CaseResult(str(index), "facts", index < 8) for index in range(10)]
    candidate = [CaseResult(str(index), "facts", index < 7) for index in range(10)]
    assert exercise_call(evaluate_release, baseline, candidate, max_regression=0.1).accepted


def test_insufficient_slice_is_not_a_pass_and_takes_precedence_over_regression() -> None:
    baseline = [CaseResult("a", "z", True), CaseResult("b", "a", True)]
    candidate = [CaseResult("a", "z", False), CaseResult("b", "a", True)]
    report = exercise_call(evaluate_release, baseline, candidate)
    assert report.reasons == ("a:insufficient-data", "z:insufficient-data")
    assert not report.accepted
    assert [item.count for item in report.slices] == [1, 1]


def test_order_independent_repeatable_and_nonmutating() -> None:
    rows = [CaseResult("b", "facts", False), CaseResult("a", "facts", True)]
    before = rows.copy()
    first = exercise_call(evaluate_release, rows, list(reversed(rows)))
    assert first == exercise_call(evaluate_release, list(reversed(rows)), rows)
    assert first.accepted
    assert first.reasons == ()
    assert rows == before


@pytest.mark.parametrize(
    ("baseline", "candidate"),
    [
        ([], []),
        ([CaseResult("a", "facts", True)], []),
        ([CaseResult("a", "facts", True)], [CaseResult("b", "facts", True)]),
        ([CaseResult("a", "facts", True)] * 2, [CaseResult("a", "facts", True)]),
        ([CaseResult("a", "facts", True)], [CaseResult("a", "facts", True)] * 2),
        ([CaseResult("a", "facts", True)], [CaseResult("a", "refusal", True)]),
        ([CaseResult(" ", "facts", True)], [CaseResult(" ", "facts", True)]),
        ([CaseResult("a", "", True)], [CaseResult("a", "", True)]),
        ([CaseResult("a", "facts", cast(bool, 1))], [CaseResult("a", "facts", True)]),
    ],
)
def test_rejects_incomplete_or_invalid_pairs(
    baseline: list[CaseResult],
    candidate: list[CaseResult],
) -> None:
    with pytest.raises(ValueError, match=r"case|slice|passed|empty|ID"):
        exercise_call(evaluate_release, baseline, candidate)


@pytest.mark.parametrize("minimum", [0, -1, True, 1.5])
def test_invalid_minimum(minimum: object) -> None:
    with pytest.raises(ValueError, match="min_cases"):
        exercise_call(evaluate_release, [], [], min_cases_per_slice=minimum)


@pytest.mark.parametrize("tolerance", [-0.1, 1.1, float("nan"), float("inf"), True])
def test_invalid_regression_tolerance(tolerance: object) -> None:
    with pytest.raises(ValueError, match="regression"):
        exercise_call(evaluate_release, [], [], max_regression=tolerance)
