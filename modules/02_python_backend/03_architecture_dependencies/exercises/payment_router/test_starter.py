from dataclasses import dataclass, field
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from roadmap_tools import exercise_call

from . import starter


@dataclass
class FakePaymentService:
    payments: dict[str, starter.Payment] = field(default_factory=dict)
    create_calls: list[starter.PaymentCreate] = field(default_factory=list)

    def create(self, payment: starter.PaymentCreate) -> starter.Payment:
        self.create_calls.append(payment)
        created = starter.Payment(
            id=f"payment-{len(self.create_calls)}",
            amount=payment.amount,
            currency=payment.currency,
            internal_note="not an API field",
        )
        self.payments[created.id] = created
        return created

    def get(self, payment_id: str) -> starter.Payment:
        try:
            return self.payments[payment_id]
        except KeyError as error:
            raise starter.PaymentNotFound from error


def create_client(service: FakePaymentService) -> TestClient:
    app = FastAPI()
    router = exercise_call(starter.build_payment_router, service)
    app.include_router(router)
    return TestClient(app)


def test_post_payment_returns_created_response_and_calls_service_once() -> None:
    service = FakePaymentService()
    client = create_client(service)

    response = client.post("/payments", json={"amount": "12.50", "currency": "USD"})

    assert response.status_code == 201
    assert response.json() == {"id": "payment-1", "amount": "12.50", "currency": "USD"}
    assert service.create_calls == [starter.PaymentCreate(amount=Decimal("12.50"), currency="USD")]


def test_get_payment_returns_service_result_and_propagates_missing_payment() -> None:
    service = FakePaymentService(
        payments={
            "payment-7": starter.Payment(
                id="payment-7",
                amount=Decimal("3.00"),
                currency="EUR",
                internal_note="internal only",
            )
        }
    )
    client = create_client(service)

    response = client.get("/payments/payment-7")

    assert response.status_code == 200
    assert response.json() == {"id": "payment-7", "amount": "3.00", "currency": "EUR"}
    with pytest.raises(starter.PaymentNotFound):
        client.get("/payments/missing")


def test_two_application_instances_use_their_own_services() -> None:
    first_service = FakePaymentService()
    second_service = FakePaymentService()
    first_client = create_client(first_service)
    second_client = create_client(second_service)

    created = first_client.post("/payments", json={"amount": "5.00", "currency": "GBP"})

    assert created.status_code == 201
    assert first_service.create_calls
    with pytest.raises(starter.PaymentNotFound):
        second_client.get(created.json()["id"])
