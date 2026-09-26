"""Budget accounting uses Decimal and checks every intermediate state."""

from decimal import Decimal
from typing import Literal, cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import BudgetEvent, BudgetReport, Reservation, summarize_budget

type LiteralKind = Literal["reserve", "settle", "cancel"]


def event(request: str, kind: str, amount: str) -> BudgetEvent:
    return BudgetEvent(request, cast("LiteralKind", kind), Decimal(amount))


def test_reservations_settlement_refunds_and_cancellation() -> None:
    events = [
        event("b", "reserve", "4"),
        event("a", "reserve", "3"),
        event("b", "settle", "2.5"),
        event("c", "reserve", "2"),
        event("a", "cancel", "0"),
    ]
    assert exercise_call(summarize_budget, Decimal("10"), events) == BudgetReport(
        Decimal("10"),
        Decimal("2.5"),
        Decimal("2"),
        Decimal("5.5"),
        (
            Reservation("a", Decimal("3"), "cancelled", None),
            Reservation("b", Decimal("4"), "settled", Decimal("2.5")),
            Reservation("c", Decimal("2"), "pending", None),
        ),
    )


def test_exact_replays_do_not_reopen_or_double_charge_terminal_requests() -> None:
    events = [
        event("a", "reserve", "0.3"),
        event("a", "reserve", "0.3"),
        event("a", "settle", "0.1"),
        event("a", "settle", "0.1"),
        event("a", "reserve", "0.3"),
        event("b", "reserve", "0.2"),
        event("b", "cancel", "0"),
        event("b", "cancel", "0"),
        event("b", "reserve", "0.2"),
    ]
    report = exercise_call(summarize_budget, Decimal("0.3"), events)
    assert (report.spent, report.held, report.available) == (
        Decimal("0.1"),
        Decimal(0),
        Decimal("0.2"),
    )
    assert [reservation.status for reservation in report.reservations] == ["settled", "cancelled"]


def test_zero_actual_cost_empty_ledger_and_input_preservation() -> None:
    assert exercise_call(summarize_budget, Decimal(0), []) == BudgetReport(
        Decimal(0),
        Decimal(0),
        Decimal(0),
        Decimal(0),
        (),
    )
    events = [event("a", "reserve", "1"), event("a", "settle", "0")]
    before = events.copy()
    first = exercise_call(summarize_budget, Decimal(1), events)
    assert first == exercise_call(summarize_budget, Decimal(1), events)
    assert first.spent == 0
    assert first.available == 1
    assert events == before


def test_overspend_is_rejected_even_if_a_later_event_would_refund_it() -> None:
    events = [event("a", "reserve", "7"), event("b", "reserve", "4"), event("a", "cancel", "0")]
    with pytest.raises(ValueError, match="budget"):
        exercise_call(summarize_budget, Decimal("10"), events)


@pytest.mark.parametrize(
    "tail",
    [
        event("a", "reserve", "4"),
        event("a", "settle", "4"),
        event("missing", "settle", "1"),
        event("missing", "cancel", "0"),
        event("a", "cancel", "1"),
        event("a", "unknown", "0"),
    ],
)
def test_conflicting_replay_missing_request_and_invalid_transition(tail: BudgetEvent) -> None:
    with pytest.raises(ValueError, match=r"amount|request|kind|reserve|cancel|settle"):
        exercise_call(summarize_budget, Decimal("10"), [event("a", "reserve", "3"), tail])


@pytest.mark.parametrize(
    ("terminal", "next_event"),
    [
        (event("a", "settle", "2"), event("a", "settle", "1")),
        (event("a", "settle", "2"), event("a", "cancel", "0")),
        (event("a", "cancel", "0"), event("a", "settle", "0")),
    ],
)
def test_terminal_reservations_cannot_change(
    terminal: BudgetEvent, next_event: BudgetEvent
) -> None:
    with pytest.raises(ValueError, match=r"request|settle|cancel|amount|terminal"):
        exercise_call(
            summarize_budget, Decimal(10), [event("a", "reserve", "3"), terminal, next_event]
        )


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity"])
def test_invalid_reserve_amount(amount: str) -> None:
    with pytest.raises(ValueError, match="amount"):
        exercise_call(summarize_budget, Decimal(10), [event("a", "reserve", amount)])


@pytest.mark.parametrize(
    ("kind", "amount"),
    [
        ("settle", Decimal("-1")),
        ("settle", Decimal("NaN")),
        ("settle", Decimal("Infinity")),
        ("settle", 0.1),
        ("cancel", Decimal("NaN")),
        ("cancel", Decimal("-1")),
        ("settle", Decimal("0.001")),
        ("reserve", Decimal("1000001")),
    ],
)
def test_every_kind_validates_its_amount(kind: str, amount: object) -> None:
    invalid = BudgetEvent("a", cast(LiteralKind, kind), cast(Decimal, amount))
    with pytest.raises(ValueError, match="amount"):
        exercise_call(summarize_budget, Decimal(10), [event("a", "reserve", "3"), invalid])


@pytest.mark.parametrize("limit", [Decimal("-1"), Decimal("NaN"), Decimal("Infinity"), 10.0])
def test_invalid_limit(limit: object) -> None:
    with pytest.raises(ValueError, match="limit"):
        exercise_call(summarize_budget, limit, [])


def test_rejects_blank_id_and_non_decimal_amount() -> None:
    with pytest.raises(ValueError, match="request"):
        exercise_call(summarize_budget, Decimal(10), [event(" ", "reserve", "1")])
    with pytest.raises(ValueError, match="amount"):
        exercise_call(
            summarize_budget, Decimal(10), [BudgetEvent("a", "reserve", cast(Decimal, 0.1))]
        )
