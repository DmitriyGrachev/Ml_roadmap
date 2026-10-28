"""Neutral boundary demo, independent of the transaction exercise."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator


class PrintBatch(BaseModel):
    quantity: int

    @field_validator("quantity", mode="after")
    @classmethod
    def complete_packs(cls, value: int) -> int:
        if value <= 0 or value % 4 != 0:
            raise ValueError("quantity must be positive and divisible by 4")
        return value


class PrintService:
    def __init__(self) -> None:
        self.accepted: list[int] = []

    def create(self, batch: PrintBatch) -> dict[str, int]:
        self.accepted.append(batch.quantity)
        return {"quantity": batch.quantity, "packs": batch.quantity // 4}


def create_app() -> tuple[FastAPI, PrintService]:
    app = FastAPI()
    service = PrintService()

    @app.post("/print-batches", status_code=201)
    def create_batch(batch: PrintBatch) -> dict[str, int]:
        return service.create(batch)

    return app, service


def main() -> None:
    app, service = create_app()
    with TestClient(app) as client:
        valid = client.post("/print-batches", json={"quantity": "8"})
        print(f"valid: {valid.status_code} {valid.json()}")
        for quantity in (6, "oops"):
            invalid = client.post("/print-batches", json={"quantity": quantity})
            error = invalid.json()["detail"][0]
            print(f"invalid {quantity!r}: {invalid.status_code} {error['loc']} {error['type']}")
    print(f"service accepted: {service.accepted}")


if __name__ == "__main__":
    main()
