"""Exercise real request parsing, conflict decisions, and application-local state."""

import pytest
from fastapi.testclient import TestClient

from roadmap_tools.exercise import exercise_call

from .starter import create_app

pytestmark = pytest.mark.student_exercise


def test_create_trims_room_and_returns_assigned_id() -> None:
    with TestClient(exercise_call(create_app)) as client:
        response = client.post("/bookings", json={"room": " Elm ", "start": 60, "end": 90})
        assert response.status_code == 201
        assert response.json() == {"id": 1, "room": "Elm", "start": 60, "end": 90}
        assert client.get("/bookings").json() == [response.json()]


def test_conflict_does_not_save_record_or_consume_id() -> None:
    with TestClient(exercise_call(create_app)) as client:
        assert (
            client.post("/bookings", json={"room": "Elm", "start": 60, "end": 90}).status_code
            == 201
        )
        conflict = client.post("/bookings", json={"room": " Elm ", "start": 70, "end": 80})
        assert conflict.status_code == 409
        response = client.post("/bookings", json={"room": "Elm", "start": 90, "end": 100})
        assert response.status_code == 201
        assert response.json()["id"] == 2
        assert len(client.get("/bookings").json()) == 2


def test_enclosing_interval_conflicts_but_other_room_does_not() -> None:
    with TestClient(exercise_call(create_app)) as client:
        client.post("/bookings", json={"room": "Elm", "start": 30, "end": 40})
        assert (
            client.post("/bookings", json={"room": "Elm", "start": 0, "end": 1440}).status_code
            == 409
        )
        assert (
            client.post("/bookings", json={"room": "Oak", "start": 0, "end": 1440}).status_code
            == 201
        )


def test_empty_state_is_per_app_and_list_follows_creation_order() -> None:
    with (
        TestClient(exercise_call(create_app)) as first,
        TestClient(exercise_call(create_app)) as second,
    ):
        assert first.get("/bookings").status_code == 200
        assert first.get("/bookings").json() == []
        first.post("/bookings", json={"room": "Z", "start": 100, "end": 110})
        first.post("/bookings", json={"room": "A", "start": 0, "end": 1})
        assert [row["room"] for row in first.get("/bookings").json()] == ["Z", "A"]
        assert second.get("/bookings").json() == []


@pytest.mark.parametrize(
    "payload",
    [
        {"room": " ", "start": 0, "end": 1},
        {"room": "A", "start": -1, "end": 1},
        {"room": "A", "start": 2, "end": 2},
        {"room": "A", "start": 3, "end": 2},
        {"room": "A", "start": 0, "end": 1441},
        {"room": "A", "start": True, "end": 2},
        {"room": "A", "start": "1", "end": 2},
        {"room": "A", "start": 1.5, "end": 2},
        {"room": "A", "start": 0},
    ],
)
def test_invalid_payload_returns_422_without_writing(payload: dict[str, object]) -> None:
    with TestClient(exercise_call(create_app)) as client:
        assert client.post("/bookings", json=payload).status_code == 422
        assert client.get("/bookings").json() == []
