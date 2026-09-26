"""Check a declared schema boundary without pretending to recognize arbitrary PII."""

from copy import deepcopy
from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import RedactedEvent, redact_events


def test_allowlist_removes_entire_unknown_fields_at_both_supported_levels() -> None:
    event: dict[str, object] = {
        "event": "request_completed",
        "timestamp_ms": 12,
        "request_id": "req-1",
        "prompt": "secret text",
        "payload": {"password": "hidden", "nested": {"token": "x"}},
        "attributes": {
            "route": "/books",
            "status_code": 200,
            "latency_ms": 2.5,
            "model_version": "v2",
            "authorization": "Bearer secret",
            "email": "a@b",
        },
    }
    assert exercise_call(redact_events, [event]) == (
        RedactedEvent(
            {
                "event": "request_completed",
                "timestamp_ms": 12,
                "request_id": "req-1",
                "attributes": {
                    "route": "/books",
                    "status_code": 200,
                    "latency_ms": 2.5,
                    "model_version": "v2",
                },
            },
            4,
        ),
    )


def test_missing_optional_fields_empty_attributes_and_order_are_preserved() -> None:
    events = [
        {"event": "provider_error", "timestamp_ms": 0},
        {"event": "cache_hit", "timestamp_ms": 0, "attributes": {}},
    ]
    result = exercise_call(redact_events, events)
    assert result == tuple(RedactedEvent(event, 0) for event in events)
    assert exercise_call(redact_events, []) == ()


def test_output_is_independent_of_inputs_and_repeated_calls() -> None:
    events: list[dict[str, object]] = [
        {"event": "cache_hit", "timestamp_ms": 1, "attributes": {"route": "/labels"}}
    ]
    before = deepcopy(events)
    first = exercise_call(redact_events, events)
    second = exercise_call(redact_events, events)
    assert first == second
    cast(dict[str, object], first[0].safe["attributes"])["route"] = "/books"
    assert events == before
    assert cast(dict[str, object], second[0].safe["attributes"])["route"] == "/labels"


@pytest.mark.parametrize(
    "patch",
    [
        {"event": "unknown"},
        {"timestamp_ms": -1},
        {"timestamp_ms": True},
        {"timestamp_ms": 1.5},
        {"request_id": " "},
        {"request_id": "x" * 65},
        {"request_id": None},
        {"attributes": []},
        {"attributes": {"route": "/books/user@example.com"}},
        {"attributes": {"status_code": 600}},
        {"attributes": {"status_code": True}},
        {"attributes": {"latency_ms": -1}},
        {"attributes": {"latency_ms": float("nan")}},
        {"attributes": {"latency_ms": float("inf")}},
        {"attributes": {"latency_ms": "2"}},
        {"attributes": {"latency_ms": True}},
        {"attributes": {"model_version": " "}},
        {"attributes": {"model_version": "x" * 33}},
    ],
)
def test_invalid_known_values_are_rejected_instead_of_silently_discarded(
    patch: dict[str, object],
) -> None:
    event = {"event": "request_completed", "timestamp_ms": 1, **patch}
    with pytest.raises(
        ValueError, match=r"event|timestamp|request|attributes|route|status|latency|model"
    ):
        exercise_call(redact_events, [event])


@pytest.mark.parametrize("event", [{}, {"event": "cache_hit"}, {"timestamp_ms": 1}])
def test_required_fields(event: dict[str, object]) -> None:
    with pytest.raises(ValueError, match=r"event|timestamp|required"):
        exercise_call(redact_events, [event])
