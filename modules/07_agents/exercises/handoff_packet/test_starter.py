"""Bound visible context without disclosing hidden facts or hidden counts."""

# ruff: noqa: PT011 -- The public contract specifies exception classes, not message text.

import pytest

from roadmap_tools import exercise_call

from .starter import HandoffFact, HandoffPacket, VisibleFact, build_handoff


def test_copies_required_metadata_and_permitted_facts_in_order() -> None:
    facts = (HandoffFact("title", "Maps", "catalog"), HandoffFact("room", "West", "catalog"))
    result = exercise_call(build_handoff, "C1", "review", facts, frozenset({"catalog"}), 40)
    assert result == HandoffPacket(
        "C1", "review", (VisibleFact("title", "Maps"), VisibleFact("room", "West")), False
    )
    assert facts == (
        HandoffFact("title", "Maps", "catalog"),
        HandoffFact("room", "West", "catalog"),
    )


def test_hidden_facts_do_not_use_budget_or_change_truncation() -> None:
    facts = (HandoffFact("private", "secret" * 100, "staff"), HandoffFact("x", "ok", "public"))
    assert exercise_call(build_handoff, "C", "R", facts, frozenset({"public"}), 5) == (
        HandoffPacket("C", "R", (VisibleFact("x", "ok"),), False)
    )


def test_truncates_first_overflowing_value_then_stops() -> None:
    facts = (
        HandoffFact("a", "abc", "read"),
        HandoffFact("b", "xyz", "read"),
        HandoffFact("c", "z", "read"),
    )
    assert exercise_call(build_handoff, "C", "R", facts, frozenset({"read"}), 8) == (
        HandoffPacket("C", "R", (VisibleFact("a", "abc"), VisibleFact("b", "x")), True)
    )


def test_name_that_cannot_fit_is_omitted_without_skipping_ahead() -> None:
    facts = (HandoffFact("long", "value", "read"), HandoffFact("a", "", "read"))
    assert exercise_call(build_handoff, "C", "R", facts, frozenset({"read"}), 3) == (
        HandoffPacket("C", "R", (), True)
    )


def test_exact_name_fit_keeps_empty_prefix_and_reports_truncation() -> None:
    assert exercise_call(
        build_handoff, "C", "R", (HandoffFact("a", "abc", "read"),), frozenset({"read"}), 3
    ) == (HandoffPacket("C", "R", (VisibleFact("a", ""),), True))


def test_budget_counts_unicode_codepoints_and_empty_values() -> None:
    facts = (HandoffFact("é", "猫", "read"), HandoffFact("b", "", "read"))
    assert exercise_call(build_handoff, "C", "R", facts, frozenset({"read"}), 5) == (
        HandoffPacket("C", "R", (VisibleFact("é", "猫"), VisibleFact("b", "")), False)
    )


def test_metadata_only_packet_and_no_authorized_facts_are_not_truncated() -> None:
    assert exercise_call(
        build_handoff, "C", "R", (HandoffFact("a", "secret", "staff"),), frozenset(), 2
    ) == HandoffPacket("C", "R", (), False)


@pytest.mark.parametrize("budget", [0, True, 4097, 1])
def test_invalid_budget_or_metadata_overflow_raises(budget: int) -> None:
    with pytest.raises(ValueError):
        exercise_call(build_handoff, "C", "R", (), frozenset(), budget)


@pytest.mark.parametrize(
    ("case_id", "reason"), [("", "R"), (" C", "R"), ("C", " "), ("C" * 81, "R"), ("C", "R" * 161)]
)
def test_required_metadata_is_validated(case_id: str, reason: str) -> None:
    with pytest.raises(ValueError):
        exercise_call(build_handoff, case_id, reason, (), frozenset(), 400)


@pytest.mark.parametrize(
    "facts",
    [
        (HandoffFact("x", "a", "read"), HandoffFact("x", "b", "staff")),
        (HandoffFact("", "a", "staff"),),
        (HandoffFact("x", "a", " staff"),),
        (HandoffFact("x" * 41, "a", "staff"),),
        (HandoffFact("x", "a", "s" * 41),),
    ],
)
def test_validates_hidden_fact_structure_too(facts: tuple[HandoffFact, ...]) -> None:
    with pytest.raises(ValueError):
        exercise_call(build_handoff, "C", "R", facts, frozenset({"read"}), 100)
