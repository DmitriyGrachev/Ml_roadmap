"""Paired release policy for a frozen set of answerable and no-answer cases."""

import math
from dataclasses import dataclass


def _nonnegative_number(name: str, value: float) -> None:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


def _nonnegative_integer(name: str, value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


@dataclass(frozen=True)
class Observation:
    case_id: str
    trace_id: str
    slice_name: str
    answerable: bool
    retrieval_hit: bool
    correct: bool
    latency_ms: float
    input_units: int
    output_units: int

    def __post_init__(self) -> None:
        for label in (self.case_id, self.trace_id, self.slice_name):
            if not isinstance(label, str) or not label.strip():
                raise ValueError("case, trace and slice identities must be nonblank strings")
        flags = (self.answerable, self.retrieval_hit, self.correct)
        if any(type(flag) is not bool for flag in flags):
            raise ValueError("case judgments must be booleans")
        _nonnegative_number("latency_ms", self.latency_ms)
        _nonnegative_integer("input_units", self.input_units)
        _nonnegative_integer("output_units", self.output_units)


def _case_index(rows: list[Observation]) -> dict[str, Observation]:
    indexed = {row.case_id: row for row in rows}
    if len(indexed) != len(rows) or len({row.trace_id for row in rows}) != len(rows):
        raise ValueError("duplicate case or trace identity")
    if {row.answerable for row in rows} != {True, False}:
        raise ValueError("both answerable and no-answer cases are required")
    return indexed


def _p95_ms(rows: list[Observation]) -> float:
    return sorted(row.latency_ms for row in rows)[math.ceil(0.95 * len(rows)) - 1]


def metrics(
    rows: list[Observation], input_price: float | None = None, output_price: float | None = None
) -> dict[str, int | float | None]:
    """Prices are USD per million units. A missing rate pair leaves cost unknown."""
    _case_index(rows)
    answerable = [row for row in rows if row.answerable]
    no_answer = [row for row in rows if not row.answerable]
    inputs = sum(row.input_units for row in rows)
    outputs = sum(row.output_units for row in rows)
    cost = None
    if input_price is not None and output_price is not None:
        _nonnegative_number("input_price", input_price)
        _nonnegative_number("output_price", output_price)
        cost = (inputs * input_price + outputs * output_price) / 1_000_000
        _nonnegative_number("estimated_cost_usd", cost)
    elif input_price is not None or output_price is not None:
        raise ValueError("input and output prices must be supplied together")
    return {
        "case_count": len(rows),
        "answerable_count": len(answerable),
        "no_answer_count": len(no_answer),
        "quality_rate": sum(row.correct for row in rows) / len(rows),
        "retrieval_hit_rate": sum(row.retrieval_hit for row in answerable) / len(answerable),
        "abstention_rate": sum(row.correct for row in no_answer) / len(no_answer),
        "latency_p95_ms": _p95_ms(rows),
        "input_units": inputs,
        "output_units": outputs,
        "estimated_cost_usd": cost,
    }


def violations(
    baseline: list[Observation],
    candidate: list[Observation],
    *,
    max_p95_ms: float | None = None,
    max_output_units: int | None = None,
) -> list[str]:
    """Require every previously correct case, every hit, and two absolute quality floors."""
    before = _case_index(baseline)
    after = _case_index(candidate)
    if before.keys() != after.keys():
        raise ValueError("baseline and candidate must cover the same case IDs")
    reasons = []
    for case_id, left in before.items():
        right = after[case_id]
        if (left.answerable, left.slice_name) != (right.answerable, right.slice_name):
            raise ValueError(f"case annotations changed: {case_id}")
        if left.correct and not right.correct:
            reasons.append(f"answer_regression:{case_id}")
        if left.answerable and left.retrieval_hit and not right.retrieval_hit:
            reasons.append(f"retrieval_regression:{case_id}")

    answerable = [row for row in candidate if row.answerable]
    if 3 * sum(row.correct for row in answerable) < 2 * len(answerable):
        reasons.append("answerable_floor")
    if any(not row.correct for row in candidate if not row.answerable):
        reasons.append("abstention_floor")
    if max_p95_ms is not None:
        _nonnegative_number("max_p95_ms", max_p95_ms)
        if _p95_ms(candidate) > max_p95_ms:
            reasons.append("latency_budget")
    if max_output_units is not None:
        _nonnegative_integer("max_output_units", max_output_units)
        if sum(row.output_units for row in candidate) > max_output_units:
            reasons.append("output_budget")
    return reasons
