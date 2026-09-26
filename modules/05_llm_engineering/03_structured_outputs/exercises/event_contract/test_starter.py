"""Reject malformed output and unsupported museum-event claims."""

import json
from datetime import timedelta

import pytest
from pydantic import ValidationError

from roadmap_tools import exercise_call

from .starter import parse_event

SOURCE = "The City Museum hosts a Moon talk on May 2. Seats available: 40."
VENUES = frozenset({"City Museum", "Science Hall"})


def payload(**updates: object) -> str:
    data: dict[str, object] = {
        "title": "Moon talk",
        "venue": "City Museum",
        "starts_at": "2026-05-02T10:00:00+02:00",
        "ends_at": "2026-05-02T11:00:00+02:00",
        "seats": 40,
        "evidence": "The City Museum hosts a Moon talk on May 2.",
    }
    data.update(updates)
    return json.dumps(data)


def test_accepts_valid_typed_event_and_preserves_timezone() -> None:
    event = exercise_call(parse_event, payload(), VENUES, SOURCE)
    assert event.title == "Moon talk"
    assert event.venue == "City Museum"
    assert event.seats == 40
    assert event.starts_at.utcoffset() == timedelta(hours=2)
    assert (event.ends_at - event.starts_at).total_seconds() == 3600


@pytest.mark.parametrize("seats", [0, 200])
def test_accepts_capacity_bounds(seats: int) -> None:
    assert exercise_call(parse_event, payload(seats=seats), VENUES, SOURCE).seats == seats


@pytest.mark.parametrize("seats", ["40", True, 40.0, -1, 201, None])
def test_rejects_coercion_and_out_of_range_capacity(seats: object) -> None:
    with pytest.raises(ValidationError):
        exercise_call(parse_event, payload(seats=seats), VENUES, SOURCE)


@pytest.mark.parametrize("raw", ["not JSON", "[]", "{}", "null"])
def test_rejects_invalid_json_or_missing_fields(raw: str) -> None:
    with pytest.raises(ValidationError):
        exercise_call(parse_event, raw, VENUES, SOURCE)


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        exercise_call(parse_event, payload(command="open-door"), VENUES, SOURCE)


@pytest.mark.parametrize(
    "updates",
    [
        {"starts_at": "2026-05-02T10:00:00"},
        {"ends_at": "2026-05-02T11:00:00"},
        {"ends_at": "2026-05-02T10:00:00+02:00"},
        {"ends_at": "2026-05-02T09:59:00+02:00"},
        {"starts_at": "yesterday"},
    ],
)
def test_requires_aware_chronological_times(updates: dict[str, object]) -> None:
    with pytest.raises(ValueError, match=r"time|starts|ends"):
        exercise_call(parse_event, payload(**updates), VENUES, SOURCE)


def test_compares_instants_across_offsets() -> None:
    event = exercise_call(parse_event, payload(ends_at="2026-05-02T09:00:00Z"), VENUES, SOURCE)
    assert (event.ends_at - event.starts_at).total_seconds() == 3600


@pytest.mark.parametrize(
    "updates",
    [
        {"title": " "},
        {"title": " Moon talk"},
        {"venue": "city museum"},
        {"venue": "City Museum "},
        {"evidence": ""},
        {"evidence": "Moon talk never happened"},
    ],
)
def test_requires_exact_venue_nonblank_trimmed_title_and_source_evidence(
    updates: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match=r"title|venue|evidence"):
        exercise_call(parse_event, payload(**updates), VENUES, SOURCE)


def test_caller_controls_allowed_venues() -> None:
    with pytest.raises(ValueError, match="venue"):
        exercise_call(parse_event, payload(), frozenset(), SOURCE)
