"""Typed schema and unfinished SQL aggregation boundary."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, select
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Normalize persisted timestamps and restore SQLite timezone metadata."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        del dialect
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone offset")
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        del dialect
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class Base(DeclarativeBase):
    """Declarative base for the query exercise's isolated schema."""


class TransactionRecord(Base):
    """Minimal transaction mapping used as query input."""

    __tablename__ = "exercise_query_transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, index=True)


@dataclass(frozen=True, slots=True)
class CurrencyTotal:
    """One currency's exact total for a requested UTC day."""

    currency: str
    total: Decimal


def daily_currency_totals(session: Session, day: date) -> list[CurrencyTotal]:
    """Aggregate one UTC day in SQL and return currency-sorted totals."""

    raise NotImplementedError("Implement daily currency totals query")


__all__ = [
    "Base",
    "CurrencyTotal",
    "TransactionRecord",
    "daily_currency_totals",
    "select",
]
