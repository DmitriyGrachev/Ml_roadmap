"""Typed SQLAlchemy infrastructure and unfinished repository operations."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Engine, Numeric, String, Uuid, create_engine
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from banking_ai_lab.domain import Transaction, TransactionStatus


class Base(DeclarativeBase):
    """Declarative metadata root for the project database."""


class ExactDecimal(Numeric[Decimal]):
    """Declare NUMERIC while avoiding SQLite's lossy float conversion."""

    cache_ok = True

    def bind_processor(self, dialect: Dialect) -> Callable[[Any], Any] | None:
        if dialect.name == "sqlite":
            return lambda value: None if value is None else f"decimal:{value}"
        return None

    def result_processor(
        self,
        dialect: Dialect,
        _coltype: object,
    ) -> Callable[[Any], Decimal | None] | None:
        def restore_decimal(value: object) -> Decimal | None:
            if value is None:
                return None
            text = str(value)
            if dialect.name == "sqlite" and text.startswith("decimal:"):
                text = text.removeprefix("decimal:")
            return Decimal(text)

        return restore_decimal


class TransactionRow(Base):
    """Database representation of a validated transaction."""

    __tablename__ = "transactions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    merchant: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    is_fraud: Mapped[bool] = mapped_column(Boolean, nullable=False)

    @classmethod
    def from_transaction(cls, transaction: Transaction) -> TransactionRow:
        """Create a persistence row without changing the immutable domain object."""
        return cls(
            id=transaction.id,
            user_id=transaction.user_id,
            amount=transaction.amount,
            currency=transaction.currency,
            merchant=transaction.merchant,
            category=transaction.category,
            timestamp=transaction.timestamp,
            status=transaction.status,
            is_fraud=transaction.is_fraud,
        )

    def to_transaction(self) -> Transaction:
        """Restore the complete domain value, including UTC lost by SQLite."""
        timestamp = self.timestamp
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        else:
            timestamp = timestamp.astimezone(UTC)
        return Transaction.model_validate(
            {
                "id": self.id,
                "user_id": self.user_id,
                "amount": self.amount,
                "currency": self.currency,
                "merchant": self.merchant,
                "category": self.category,
                "timestamp": timestamp,
                "status": self.status,
                "is_fraud": self.is_fraud,
            }
        )


def create_database_engine(database_url: str) -> Engine:
    """Construct an engine without opening a database connection."""
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create the typed session factory injected into repositories."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_schema(engine: Engine) -> None:
    """Create project tables explicitly; application construction never calls this."""
    Base.metadata.create_all(engine)


class SqlAlchemyTransactionRepository:
    """SQLAlchemy repository whose persistence algorithms are learner exercises."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create_transaction(self, transaction: Transaction) -> Transaction:
        """Insert atomically, translate duplicates, and always roll back/close on failure."""
        raise NotImplementedError("insert a transaction with safe session cleanup")

    def get_transaction(self, transaction_id: UUID) -> Transaction | None:
        """Load and map one transaction while always closing the session."""
        raise NotImplementedError("load a transaction with safe session cleanup")

    def list_transactions(
        self,
        *,
        offset: int,
        limit: int | None,
        user_id: str | None,
        status: TransactionStatus | None,
    ) -> tuple[Transaction, ...]:
        """Filter, then order by timestamp/ID, page, map, and close the session."""
        raise NotImplementedError("list transactions with safe session cleanup")
