"""Deliberately coupled API fixture for a test-design code review."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_id: str
    amount: str
    currency: str


class PaymentResponse(PaymentCreate):
    status: str


class ReviewPaymentService:
    def __init__(self) -> None:
        self.payments: dict[str, PaymentResponse] = {}

    def create(self, payment: PaymentCreate) -> PaymentResponse:
        created = PaymentResponse(**payment.model_dump(), status="accepted")
        self.payments[created.payment_id] = created
        return created

    def get(self, payment_id: str) -> PaymentResponse:
        try:
            return self.payments[payment_id]
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error


def get_payment_service() -> ReviewPaymentService:
    return ReviewPaymentService()


shared_service = ReviewPaymentService()
app = FastAPI(title="Coupled payment review fixture")


@app.post(
    "/review-payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payment: PaymentCreate,
    service: Annotated[ReviewPaymentService, Depends(get_payment_service)],
) -> PaymentResponse:
    return service.create(payment)


@app.get("/review-payments/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    service: Annotated[ReviewPaymentService, Depends(get_payment_service)],
) -> PaymentResponse:
    return service.get(payment_id)
