from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from roadmap_tools import exercise_call

from . import starter


def validate(payload: dict[str, object]) -> starter.TransactionCreate:
    return exercise_call(starter.validate_transaction, payload)


def transaction_client() -> TestClient:
    validate(
        {
            "amount": "1.00",
            "currency": "USD",
            "merchant": "Market",
            "timestamp": "2026-09-19T10:15:00Z",
        }
    )
    app = FastAPI()

    @app.post("/transactions")
    def create_transaction(transaction: starter.TransactionCreate) -> dict[str, bool]:
        return {"accepted": bool(transaction)}

    return TestClient(app)


@pytest.mark.parametrize("currency", ["USD", "EUR", "GBP", "MDL"])
def test_valid_transaction_preserves_decimal_and_serializes_exact_json(currency: str) -> None:
    transaction = validate(
        {
            "amount": "12.50",
            "currency": currency,
            "merchant": "Library Cafe",
            "timestamp": "2026-09-19T10:15:00Z",
        }
    )

    assert transaction.amount == Decimal("12.50")
    assert isinstance(transaction.amount, Decimal)
    assert transaction.model_dump(mode="json") == {
        "amount": "12.50",
        "currency": currency,
        "merchant": "Library Cafe",
        "timestamp": "2026-09-19T10:15:00Z",
    }


def test_transaction_schema_exposes_documented_example() -> None:
    transaction = validate(
        {
            "amount": "12.50",
            "currency": "USD",
            "merchant": "Library Cafe",
            "timestamp": "2026-09-19T10:15:00Z",
        }
    )

    assert transaction.timestamp == datetime(2026, 9, 19, 10, 15, tzinfo=UTC)
    assert transaction.model_json_schema()["examples"] == [
        {
            "amount": "12.50",
            "currency": "USD",
            "merchant": "Library Cafe",
            "timestamp": "2026-09-19T10:15:00Z",
        }
    ]


def test_currency_is_normalized_to_uppercase() -> None:
    transaction = validate(
        {
            "amount": "1.00",
            "currency": "mDl",
            "merchant": "Market",
            "timestamp": "2026-09-19T10:15:00+00:00",
        }
    )

    assert transaction.currency == "MDL"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "amount": "0",
            "currency": "USD",
            "merchant": "Market",
            "timestamp": "2026-09-19T10:15:00Z",
        },
        {
            "amount": "-0.01",
            "currency": "USD",
            "merchant": "Market",
            "timestamp": "2026-09-19T10:15:00Z",
        },
        {
            "amount": "1.00",
            "currency": "RON",
            "merchant": "Market",
            "timestamp": "2026-09-19T10:15:00Z",
        },
        {
            "amount": "1.00",
            "currency": "USD",
            "merchant": "  ",
            "timestamp": "2026-09-19T10:15:00Z",
        },
        {
            "amount": "1.00",
            "currency": "USD",
            "merchant": "Market",
            "timestamp": "2026-09-19T10:15:00",
        },
        {
            "amount": "1.00",
            "currency": "USD",
            "merchant": "Market",
            "timestamp": "2026-09-19T10:15:00Z",
            "account_number": "never accepted",
        },
    ],
    ids=[
        "zero-amount",
        "negative-amount",
        "unknown-currency",
        "blank-merchant",
        "naive-time",
        "extra-field",
    ],
)
def test_invalid_transaction_is_a_real_validation_error(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        validate(payload)


def test_http_422_identifies_every_invalid_field() -> None:
    response = transaction_client().post(
        "/transactions",
        json={
            "amount": "0",
            "currency": "RON",
            "merchant": "Market",
            "timestamp": "2026-09-19T10:15:00",
        },
    )

    assert response.status_code == 422
    locations = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert locations >= {
        ("body", "amount"),
        ("body", "currency"),
        ("body", "timestamp"),
    }
