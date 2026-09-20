"""Immutable transaction domain contracts shared by every project stage."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

type Currency = Literal["EUR", "GBP", "MDL", "USD"]
type TransactionStatus = Literal["approved", "declined", "pending", "refunded"]

CURRENCIES: tuple[Currency, ...] = ("EUR", "GBP", "MDL", "USD")
STATUSES: tuple[TransactionStatus, ...] = (
    "approved",
    "declined",
    "pending",
    "refunded",
)
TRANSACTION_COLUMNS: tuple[str, ...] = (
    "id",
    "user_id",
    "amount",
    "currency",
    "merchant",
    "category",
    "timestamp",
    "status",
    "is_fraud",
)


class Transaction(BaseModel):
    """One validated, entirely synthetic banking transaction."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        hide_input_in_errors=True,
        allow_inf_nan=False,
    )

    id: UUID
    user_id: str = Field(repr=False)
    amount: Decimal
    currency: Currency
    merchant: str
    category: str | None = None
    timestamp: datetime
    status: TransactionStatus
    is_fraud: StrictBool

    @field_validator("user_id", "merchant")
    @classmethod
    def require_nonblank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be nonblank")
        return value

    @field_validator("category")
    @classmethod
    def require_nonblank_category(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("category must be nonblank when present")
        return value

    @field_validator("amount", mode="before")
    @classmethod
    def reject_binary_floating_point(cls, value: object) -> object:
        if isinstance(value, (bool, float)):
            raise ValueError("amount must use Decimal or decimal text")
        return value

    @field_validator("amount")
    @classmethod
    def require_positive_two_decimal_amount(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value <= 0:
            raise ValueError("amount must be finite and strictly positive")
        exponent = value.as_tuple().exponent
        if not isinstance(exponent, int) or exponent < -2:
            raise ValueError("amount must have at most two fractional digits")
        return value

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp_to_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(UTC)
