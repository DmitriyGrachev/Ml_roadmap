"""Student-owned service boundaries and their explicit repository contract."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from banking_ai_lab.domain import Transaction, TransactionStatus


class DuplicateTransactionError(Exception):
    """Signal a duplicate transaction without exposing persistence details."""

    def __init__(self, transaction_id: UUID, *, internal_detail: str | None = None) -> None:
        super().__init__("transaction already exists")
        self.transaction_id = transaction_id
        self.internal_detail = internal_detail


class TransactionNotFoundError(Exception):
    """Signal a missing transaction without exposing persistence details."""

    def __init__(self, transaction_id: UUID, *, internal_detail: str | None = None) -> None:
        super().__init__("transaction not found")
        self.transaction_id = transaction_id
        self.internal_detail = internal_detail


class TransactionRepository(Protocol):
    """Persistence operations required by the transaction service."""

    def create_transaction(self, transaction: Transaction) -> Transaction:
        """Persist and return *transaction*, or raise ``DuplicateTransactionError``."""
        ...

    def get_transaction(self, transaction_id: UUID) -> Transaction | None:
        """Return one transaction by ID, or ``None`` when it does not exist."""
        ...

    def list_transactions(
        self,
        *,
        offset: int,
        limit: int | None,
        user_id: str | None,
        status: TransactionStatus | None,
    ) -> tuple[Transaction, ...]:
        """Return a timestamp/ID-ordered filtered page without mutating stored records."""
        ...


class TransactionService:
    """Application service whose business operations are completed by the learner."""

    def __init__(self, repository: TransactionRepository) -> None:
        self.repository = repository

    def create_transaction(self, transaction: Transaction) -> Transaction:
        """Create and return a transaction, preserving duplicate-domain errors."""
        raise NotImplementedError("create a transaction through the repository")

    def get_transaction(self, transaction_id: UUID) -> Transaction:
        """Return one transaction or raise ``TransactionNotFoundError`` for an unknown ID."""
        raise NotImplementedError("get a transaction and translate a missing result")

    def list_transactions(
        self,
        *,
        offset: int,
        limit: int | None,
        user_id: str | None,
        status: TransactionStatus | None,
    ) -> tuple[Transaction, ...]:
        """Return the stable repository page for the explicit filters and bounds."""
        raise NotImplementedError("list transactions through the repository")
