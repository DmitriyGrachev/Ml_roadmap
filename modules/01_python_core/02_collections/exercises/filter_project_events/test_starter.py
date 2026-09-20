"""Tests for the filter-and-project-events student exercise."""

import pytest

from roadmap_tools import exercise_call

from .starter import EventRow, active_event_ids


def event(event_id: str, event_type: str, *, active: bool = True) -> EventRow:
    return {"id": event_id, "type": event_type, "active": active}


@pytest.mark.student_exercise
def test_active_event_ids_filters_and_projects_in_input_order() -> None:
    events = (
        item
        for item in (
            event("evt-3", "transfer"),
            event("evt-2", "payment", active=False),
            event("evt-1", "payment"),
            event("evt-4", "login"),
        )
    )

    assert exercise_call(active_event_ids, events, {"payment", "transfer"}) == [
        "evt-3",
        "evt-1",
    ]


@pytest.mark.student_exercise
def test_active_event_ids_ignores_types_that_are_not_allowed() -> None:
    assert exercise_call(active_event_ids, [event("evt-1", "login")], {"payment"}) == []


@pytest.mark.student_exercise
def test_active_event_ids_returns_empty_list_for_empty_allowed_types() -> None:
    assert exercise_call(active_event_ids, [event("evt-1", "payment")], set()) == []


@pytest.mark.student_exercise
def test_active_event_ids_returns_empty_list_for_empty_events() -> None:
    assert exercise_call(active_event_ids, [], {"payment"}) == []


def test_active_event_ids_rejects_blank_event_ids() -> None:
    with pytest.raises(ValueError, match="event ID"):
        exercise_call(active_event_ids, [event(" ", "payment")], {"payment"})


def test_active_event_ids_rejects_non_string_event_types() -> None:
    invalid_event = {"id": "evt-1", "type": 42, "active": True}

    with pytest.raises(ValueError, match="event type"):
        exercise_call(active_event_ids, [invalid_event], {"payment"})


def test_active_event_ids_rejects_non_boolean_active_flags() -> None:
    invalid_event = {"id": "evt-1", "type": "payment", "active": 1}

    with pytest.raises(ValueError, match="active flag"):
        exercise_call(active_event_ids, [invalid_event], {"payment"})
