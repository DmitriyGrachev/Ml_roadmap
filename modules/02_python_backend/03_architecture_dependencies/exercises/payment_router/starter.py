"""Starter boundary for the explicit payment-router exercise."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from fastapi import APIRouter
from pydantic import BaseModel


class PaymentCreate(BaseModel):
    """The minimal request model accepted by the router exercise."""

    amount: Decimal
    currency: str


@dataclass(frozen=True)
class Payment:
    """A service result that deliberately includes a non-public field."""

    id: str
    amount: Decimal
    currency: str
    internal_note: str


class PaymentNotFound(Exception):
    """Raised by a service when a payment cannot be found."""


class PaymentService(Protocol):
    """The external boundary the router receives explicitly."""

    def create(self, payment: PaymentCreate) -> Payment: ...

    def get(self, payment_id: str) -> Payment: ...


def build_payment_router(service: PaymentService) -> APIRouter:
    """Build routes around the supplied service without global state."""

    raise NotImplementedError("Implement payment router composition")
