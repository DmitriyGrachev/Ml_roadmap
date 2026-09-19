from fastapi.testclient import TestClient

from support_api.app import create_app
from support_api.models import TicketCreate
from support_api.service import TicketService


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


def test_falsey_injected_service_keeps_its_seeded_ticket() -> None:
    class FalseyTicketService(TicketService):
        def __bool__(self) -> bool:
            return False

    service = FalseyTicketService()
    seeded_ticket = service.create(
        TicketCreate(subject="Existing ticket", description="Created before the app."),
    )
    client = TestClient(create_app(service))

    response = client.get(f"/tickets/{seeded_ticket.id}")

    assert response.status_code == 200
    assert response.json() == seeded_ticket.model_dump()


def test_application_instances_keep_ticket_state_independent() -> None:
    first_client = TestClient(create_app())
    second_client = TestClient(create_app())

    created = first_client.post(
        "/tickets",
        json={"subject": "First application", "description": "Only stored here."},
    )

    assert created.status_code == 201
    ticket_id = created.json()["id"]
    first_response = first_client.get(f"/tickets/{ticket_id}")
    second_response = second_client.get(f"/tickets/{ticket_id}")

    assert first_response.status_code == 200
    assert second_response.status_code == 404
