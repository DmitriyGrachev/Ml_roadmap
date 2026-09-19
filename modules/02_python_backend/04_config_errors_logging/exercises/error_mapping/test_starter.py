from fastapi import FastAPI
from fastapi.testclient import TestClient

from roadmap_tools import exercise_call  # type: ignore[import-untyped]

from . import starter


def create_client() -> tuple[FastAPI, TestClient]:
    app = FastAPI()
    exercise_call(starter.register_payment_exception_handlers, app)

    @app.get("/missing")
    def missing() -> None:
        raise starter.PaymentNotFound

    @app.post("/conflict")
    def conflict() -> None:
        raise starter.PaymentConflict

    return app, TestClient(app)


def test_missing_payment_has_stable_payload_and_propagates_request_id() -> None:
    app, client = create_client()
    try:
        response = client.get("/missing", headers={"X-Request-ID": "request-42"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "code": "payment_not_found",
        "message": "Payment was not found",
        "request_id": "request-42",
    }


def test_conflict_uses_documented_fallback_request_id() -> None:
    app, client = create_client()
    try:
        response = client.post("/conflict")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "code": "payment_conflict",
        "message": "Payment conflicts with the current state",
        "request_id": "request-id-not-provided",
    }
