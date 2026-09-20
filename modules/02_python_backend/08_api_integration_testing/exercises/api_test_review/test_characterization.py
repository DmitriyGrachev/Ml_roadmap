from dataclasses import dataclass
from typing import Literal

import pytest
from fastapi.testclient import TestClient

from . import review_me


@dataclass(frozen=True)
class ApiAction:
    method: Literal["GET", "POST"]
    path: str
    body: dict[str, str] | None
    status_code: int
    response_json: dict[str, str]


@pytest.fixture
def client() -> TestClient:
    review_me.app.dependency_overrides[review_me.get_payment_service] = lambda: (
        review_me.shared_service
    )
    return TestClient(review_me.app)


@pytest.mark.parametrize(
    "actions",
    [
        (
            ApiAction(
                "POST",
                "/review-payments",
                {"payment_id": "review-alpha", "amount": "12.50", "currency": "USD"},
                201,
                {
                    "payment_id": "review-alpha",
                    "amount": "12.50",
                    "currency": "USD",
                    "status": "accepted",
                },
            ),
            ApiAction(
                "GET",
                "/review-payments/review-alpha",
                None,
                200,
                {
                    "payment_id": "review-alpha",
                    "amount": "12.50",
                    "currency": "USD",
                    "status": "accepted",
                },
            ),
            ApiAction(
                "POST",
                "/review-payments",
                {"payment_id": "review-beta", "amount": "7.25", "currency": "EUR"},
                201,
                {
                    "payment_id": "review-beta",
                    "amount": "7.25",
                    "currency": "EUR",
                    "status": "accepted",
                },
            ),
        ),
        (
            ApiAction(
                "POST",
                "/review-payments",
                {"payment_id": "review-delta", "amount": "3.00", "currency": "GBP"},
                201,
                {
                    "payment_id": "review-delta",
                    "amount": "3.00",
                    "currency": "GBP",
                    "status": "accepted",
                },
            ),
            ApiAction(
                "POST",
                "/review-payments",
                {"payment_id": "review-gamma", "amount": "5.10", "currency": "MDL"},
                201,
                {
                    "payment_id": "review-gamma",
                    "amount": "5.10",
                    "currency": "MDL",
                    "status": "accepted",
                },
            ),
            ApiAction(
                "GET",
                "/review-payments/review-gamma",
                None,
                200,
                {
                    "payment_id": "review-gamma",
                    "amount": "5.10",
                    "currency": "MDL",
                    "status": "accepted",
                },
            ),
            ApiAction(
                "GET",
                "/review-payments/review-delta",
                None,
                200,
                {
                    "payment_id": "review-delta",
                    "amount": "3.00",
                    "currency": "GBP",
                    "status": "accepted",
                },
            ),
        ),
    ],
    ids=["create-read-create", "create-create-read-reverse"],
)
def test_review_api_preserves_status_and_complete_payloads(
    client: TestClient, actions: tuple[ApiAction, ...]
) -> None:
    for action in actions:
        response = client.request(action.method, action.path, json=action.body)

        assert response.status_code == action.status_code
        assert response.json() == action.response_json
