"""Typed schema and unfinished repository boundary for the persistence exercise."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, select
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker, validates
from sqlalchemy.types import TypeDecorator


def _utc_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone offset")
    return value.astimezone(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """Store UTC and restore SQLite's otherwise-lost timezone metadata."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        del dialect
        return None if value is None else _utc_timestamp(value)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        del dialect
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class Base(DeclarativeBase):
    """Declarative base for the exercise schema."""


class TransactionRecord(Base):
    """Persisted transaction with exact money and an explicit UTC timestamp."""

    __tablename__ = "exercise_transactions"
    __table_args__ = (
        CheckConstraint("length(trim(user_id)) > 0", name="ck_transaction_user_nonblank"),
        CheckConstraint("length(currency) = 3", name="ck_transaction_currency_length"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, index=True)

    @validates("id", "user_id")
    def _validate_nonblank(self, key: str, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{key} must be a string")
        if not value.strip():
            raise ValueError(f"{key} must not be blank")
        return value

    @validates("amount")
    def _validate_amount(self, key: str, value: Decimal) -> Decimal:
        del key
        if not isinstance(value, Decimal):
            raise TypeError("amount must be a Decimal")
        return value

    @validates("currency")
    def _validate_currency(self, key: str, value: str) -> str:
        del key
        if len(value) != 3 or not value.isalpha() or value != value.upper():
            raise ValueError("currency must be three uppercase letters")
        return value

    @validates("timestamp")
    def _validate_timestamp(self, key: str, value: datetime) -> datetime:
        del key
        return _utc_timestamp(value)


class SqlAlchemyTransactionRepository:
    """Exercise boundary: implement each operation with its own session."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, record: TransactionRecord) -> TransactionRecord:
        """Persist one record, committing on success and rolling back errors."""

        raise NotImplementedError("Implement transaction repository add")

    def get(self, transaction_id: str) -> TransactionRecord | None:
        """Return one record by its stable ID, or ``None`` when absent."""

        raise NotImplementedError("Implement transaction repository get")

    def list_by_user(self, user_id: str) -> list[TransactionRecord]:
        """Return a user's records ordered by timestamp and then ID."""

        raise NotImplementedError("Implement transaction repository list_by_user")


__all__ = [
    "Base",
    "SqlAlchemyTransactionRepository",
    "TransactionRecord",
    "select",
]
