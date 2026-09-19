"""Starter boundary for the transaction-contract exercise."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TransactionCreate(BaseModel):
    """Define the request contract used to create a transaction."""

    amount: Decimal
    currency: str
    merchant: str
    timestamp: datetime


def validate_transaction(payload: Mapping[str, object]) -> TransactionCreate:
    """Validate one API payload and return its typed transaction contract."""

    raise NotImplementedError("Implement transaction contract validation")
