"""Starter boundary for stable payment API error mappings."""

from fastapi import FastAPI


class PaymentNotFound(Exception):
    """Raised when a requested payment is absent."""


class PaymentConflict(Exception):
    """Raised when a payment change conflicts with current state."""


def register_payment_exception_handlers(app: FastAPI) -> None:
    """Register stable HTTP responses for expected payment domain errors."""

    raise NotImplementedError("Implement payment exception handlers")
