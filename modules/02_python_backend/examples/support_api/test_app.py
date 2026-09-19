from fastapi.testclient import TestClient

from support_api.app import create_app


def test_health_reports_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_ticket_returns_generated_identifier() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tickets",
        json={"subject": "Cannot sign in", "description": "The reset link expired."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["subject"] == "Cannot sign in"
    assert body["description"] == "The reset link expired."


def test_create_ticket_rejects_blank_subject() -> None:
    client = TestClient(create_app())

    response = client.post("/tickets", json={"subject": "", "description": "A detail."})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "subject"]


def test_missing_ticket_returns_stable_error_payload() -> None:
    client = TestClient(create_app())

    response = client.get("/tickets/missing-ticket")

    assert response.status_code == 404
    assert response.json() == {
        "code": "ticket_not_found",
        "message": "Ticket was not found",
    }


def test_application_instances_keep_ticket_state_independent() -> None:
    first_client = TestClient(create_app())
    second_client = TestClient(create_app())

    created = first_client.post(
        "/tickets",
        json={"subject": "First application", "description": "Only stored here."},
    )

    assert created.status_code == 201
    response = second_client.get(f"/tickets/{created.json()['id']}")
    assert response.status_code == 404
