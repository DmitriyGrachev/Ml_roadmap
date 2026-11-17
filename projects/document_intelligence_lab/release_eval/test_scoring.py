from dataclasses import replace

import pytest

from projects.document_intelligence_lab.release_eval.scoring import Observation, metrics, violations


def observations() -> list[Observation]:
    return [
        Observation("a", "t1", "lookup", True, True, True, 10, 100, 20),
        Observation("b", "t2", "lookup", True, True, True, 20, 100, 20),
        Observation("c", "t3", "lookup", True, False, False, 70, 40, 0),
        Observation("x", "t4", "absent", False, False, True, 1, 0, 0),
        Observation("y", "t5", "protected", False, False, True, 2, 0, 0),
    ]


def test_metrics_use_the_correct_denominators_and_per_million_prices() -> None:
    result = metrics(observations(), 1.0, 3.0)
    assert result["case_count"] == 5
    assert result["answerable_count"] == 3
    assert result["no_answer_count"] == 2
    assert result["quality_rate"] == 4 / 5
    assert result["retrieval_hit_rate"] == 2 / 3
    assert result["abstention_rate"] == 1
    assert result["latency_p95_ms"] == 70
    assert result["estimated_cost_usd"] == pytest.approx(0.00036)
    assert metrics(observations(), None, None)["estimated_cost_usd"] is None


def test_paired_gate_accepts_permuted_results_and_equal_budget_limits() -> None:
    rows = observations()
    assert violations(rows, rows[::-1], max_p95_ms=70, max_output_units=40) == []
    assert len(violations(rows, rows, max_p95_ms=69, max_output_units=39)) == 2


def test_gate_reports_regressed_case_even_if_aggregate_improves_elsewhere() -> None:
    baseline = observations()
    candidate = baseline.copy()
    candidate[0] = replace(candidate[0], correct=False, retrieval_hit=False)
    candidate[2] = replace(candidate[2], correct=True, retrieval_hit=True)
    assert violations(baseline, candidate) == ["answer_regression:a", "retrieval_regression:a"]


def test_identical_weak_releases_still_fail_absolute_floors() -> None:
    rows = observations()
    rows[0] = replace(rows[0], correct=False)
    rows[-1] = replace(rows[-1], correct=False)
    assert set(violations(rows, rows)) == {"answerable_floor", "abstention_floor"}


def test_missing_duplicated_or_relabeled_cases_fail_closed() -> None:
    rows = observations()
    for invalid in (rows[1:], [*rows, rows[0]], [replace(rows[0], slice_name="other"), *rows[1:]]):
        with pytest.raises(ValueError, match="case"):
            violations(rows, invalid)
    with pytest.raises(ValueError, match="both"):
        metrics(rows[:3], None, None)


def test_rejects_missing_prices_or_invalid_measurements_and_budgets() -> None:
    rows = observations()
    with pytest.raises(ValueError, match="prices"):
        metrics(rows, 1, None)
    with pytest.raises(ValueError, match="finite"):
        metrics(rows, float("nan"), 1)
    with pytest.raises(ValueError, match="finite"):
        violations(rows, rows, max_p95_ms=float("inf"))
    with pytest.raises(ValueError, match="integer"):
        violations(rows, rows, max_output_units=-1)
    with pytest.raises(ValueError, match="finite"):
        metrics([replace(rows[0], latency_ms=float("nan")), *rows[1:]], None, None)
    with pytest.raises(ValueError, match="integer"):
        metrics([replace(rows[0], output_units=True), *rows[1:]], None, None)
