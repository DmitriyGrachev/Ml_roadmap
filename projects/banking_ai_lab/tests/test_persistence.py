"""Stage 5 SQLAlchemy metadata and repository acceptance contracts."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar, cast
from uuid import UUID

import pytest
from banking_ai_lab.domain import Transaction, TransactionStatus
from banking_ai_lab.persistence import (
    Base,
    ExactDecimal,
    SqlAlchemyTransactionRepository,
    TransactionRow,
    create_database_engine,
    create_schema,
    create_session_factory,
)
from banking_ai_lab.service import DuplicateTransactionError
from sqlalchemy import DateTime, Engine, Numeric, func, select
from sqlalchemy.dialects import sqlite
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from roadmap_tools import exercise_call


def make_transaction(
    index: int,
    *,
    amount: str = "10.25",
    currency: str = "EUR",
    user_id: str | None = None,
    timestamp: datetime | None = None,
    status: str = "approved",
    category: str | None = "groceries",
    is_fraud: bool = False,
) -> Transaction:
    return Transaction.model_validate(
        {
            "id": UUID(int=index),
            "user_id": user_id or f"user-{index:04d}",
            "amount": Decimal(amount),
            "currency": currency,
            "merchant": f"Merchant {index}",
            "category": category,
            "timestamp": timestamp or datetime(2025, 1, index, 10, tzinfo=UTC),
            "status": status,
            "is_fraud": is_fraud,
        }
    )


@dataclass(frozen=True)
class SqliteStore:
    engine: Engine
    sessions: sessionmaker[Session]


@pytest.fixture
def sqlite_store(tmp_path: Path) -> Iterator[SqliteStore]:
    engine = create_database_engine(f"sqlite:///{(tmp_path / 'transactions.db').as_posix()}")
    sessions = create_session_factory(engine)
    create_schema(engine)
    try:
        yield SqliteStore(engine=engine, sessions=sessions)
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def seed_transactions(
    sessions: sessionmaker[Session],
    *transactions: Transaction,
) -> None:
    with sessions() as session:
        session.add_all(TransactionRow.from_transaction(item) for item in transactions)
        session.commit()


def load_transactions_directly(sessions: sessionmaker[Session]) -> tuple[Transaction, ...]:
    with sessions() as session:
        rows = session.scalars(
            select(TransactionRow).order_by(TransactionRow.timestamp, TransactionRow.id)
        ).all()
        return tuple(row.to_transaction() for row in rows)


class TrackingSession(Session):
    instances: ClassVar[list[TrackingSession]] = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.rollback_count = 0
        self.close_count = 0
        type(self).instances.append(self)

    def rollback(self) -> None:
        self.rollback_count += 1
        super().rollback()

    def close(self) -> None:
        self.close_count += 1
        super().close()


def tracking_factory(engine: Engine) -> sessionmaker[Session]:
    TrackingSession.instances.clear()
    return cast(
        sessionmaker[Session],
        sessionmaker(
            bind=engine,
            class_=TrackingSession,
            expire_on_commit=False,
        ),
    )


class FailingSession:
    def __init__(self, original: BaseException, *, operation: str) -> None:
        self.original = original
        self.operation = operation
        self.rollback_count = 0
        self.close_count = 0

    def add(self, _row: object) -> None:
        if self.operation == "write":
            raise self.original

    def commit(self) -> None:
        if self.operation == "write":
            raise self.original

    def get(self, _entity: object, _identity: object) -> None:
        if self.operation == "get":
            raise self.original

    def scalars(self, _statement: object) -> None:
        if self.operation == "list":
            raise self.original

    def execute(self, _statement: object) -> None:
        if self.operation in {"get", "list"}:
            raise self.original

    def rollback(self) -> None:
        self.rollback_count += 1
        raise RuntimeError("rollback cleanup must not replace the original failure")

    def close(self) -> None:
        self.close_count += 1
        raise RuntimeError("close cleanup must not replace the original failure")


class FailingSessionFactory:
    def __init__(self, session: FailingSession) -> None:
        self.session = session

    def __call__(self) -> FailingSession:
        return self.session


def test_sqlalchemy_metadata_uses_typed_money_timestamp_and_complete_columns() -> None:
    columns = TransactionRow.__table__.columns

    assert tuple(columns.keys()) == (
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
    assert columns["id"].primary_key
    assert isinstance(columns["amount"].type, ExactDecimal)
    assert isinstance(columns["amount"].type, Numeric)
    assert columns["amount"].type.asdecimal is True
    assert str(columns["amount"].type.compile(dialect=sqlite.dialect())).startswith("NUMERIC")
    assert isinstance(columns["timestamp"].type, DateTime)
    assert columns["timestamp"].type.timezone is True
    assert columns["category"].nullable is True
    assert columns["user_id"].nullable is False


def test_model_mapping_preserves_exact_decimal_and_restores_utc_after_sqlite_round_trip(
    sqlite_store: SqliteStore,
) -> None:
    large_source = make_transaction(
        1,
        amount="1234567890123456789012345678.91",
        currency="MDL",
        timestamp=datetime(2025, 2, 3, 4, 5, 6, tzinfo=UTC),
        status="refunded",
        category=None,
        is_fraud=True,
    )
    scaled_source = make_transaction(
        2,
        amount="0.10",
        timestamp=datetime(2025, 2, 3, 4, 5, 7, tzinfo=UTC),
    )
    seed_transactions(sqlite_store.sessions, large_source, scaled_source)

    loaded = load_transactions_directly(sqlite_store.sessions)

    assert loaded == (large_source, scaled_source)
    assert str(loaded[0].amount) == "1234567890123456789012345678.91"
    assert str(loaded[1].amount) == "0.10"
    assert all(item.timestamp.tzinfo is UTC for item in loaded)


@pytest.mark.student_exercise
def test_repository_create_inserts_one_complete_transaction_and_closes_session(
    sqlite_store: SqliteStore,
) -> None:
    sessions = tracking_factory(sqlite_store.engine)
    repository = SqlAlchemyTransactionRepository(sessions)
    transaction = make_transaction(1, amount="0.10", category=None, is_fraud=True)

    created = exercise_call(repository.create_transaction, transaction)

    assert created == transaction
    assert load_transactions_directly(sqlite_store.sessions) == (transaction,)
    assert len(TrackingSession.instances) == 1
    assert TrackingSession.instances[0].close_count >= 1


@pytest.mark.student_exercise
def test_repository_get_maps_a_directly_seeded_row_and_closes_session(
    sqlite_store: SqliteStore,
) -> None:
    transaction = make_transaction(
        7,
        amount="88.40",
        currency="GBP",
        timestamp=datetime(2025, 5, 6, 7, 8, tzinfo=UTC),
        status="pending",
    )
    seed_transactions(sqlite_store.sessions, transaction)
    sessions = tracking_factory(sqlite_store.engine)
    repository = SqlAlchemyTransactionRepository(sessions)

    loaded = exercise_call(repository.get_transaction, transaction.id)

    assert loaded == transaction
    assert loaded is not transaction
    assert loaded.timestamp.tzinfo is UTC
    assert len(TrackingSession.instances) == 1
    assert TrackingSession.instances[0].close_count >= 1


@pytest.mark.student_exercise
def test_repository_get_returns_none_for_an_unknown_id(sqlite_store: SqliteStore) -> None:
    sessions = tracking_factory(sqlite_store.engine)
    repository = SqlAlchemyTransactionRepository(sessions)

    loaded = exercise_call(repository.get_transaction, UUID(int=999))

    assert loaded is None
    assert len(TrackingSession.instances) == 1
    assert TrackingSession.instances[0].close_count >= 1


@pytest.mark.student_exercise
def test_repository_list_is_stably_ordered_and_uses_bounded_pagination(
    sqlite_store: SqliteStore,
) -> None:
    late = make_transaction(9, timestamp=datetime(2025, 1, 2, tzinfo=UTC))
    latest = make_transaction(10, timestamp=datetime(2025, 1, 3, tzinfo=UTC))
    same_time_high_id = make_transaction(5, timestamp=datetime(2025, 1, 1, tzinfo=UTC))
    same_time_low_id = make_transaction(1, timestamp=datetime(2025, 1, 1, tzinfo=UTC))
    seed_transactions(
        sqlite_store.sessions,
        latest,
        late,
        same_time_high_id,
        same_time_low_id,
    )
    sessions = tracking_factory(sqlite_store.engine)
    repository = SqlAlchemyTransactionRepository(sessions)

    page = exercise_call(
        repository.list_transactions,
        offset=1,
        limit=2,
        user_id=None,
        status=None,
    )
    assert page == (same_time_high_id, late)
    assert len(TrackingSession.instances) == 1
    assert TrackingSession.instances[0].close_count >= 1


@pytest.mark.student_exercise
def test_repository_list_supports_an_unbounded_page(
    sqlite_store: SqliteStore,
) -> None:
    first = make_transaction(1)
    second = make_transaction(2)
    seed_transactions(sqlite_store.sessions, first, second)
    repository = SqlAlchemyTransactionRepository(sqlite_store.sessions)

    all_rows = exercise_call(
        repository.list_transactions,
        offset=0,
        limit=None,
        user_id=None,
        status=None,
    )
    assert all_rows == (first, second)


@pytest.mark.student_exercise
def test_repository_list_returns_an_empty_page_after_the_last_row(
    sqlite_store: SqliteStore,
) -> None:
    first = make_transaction(1)
    second = make_transaction(2)
    seed_transactions(sqlite_store.sessions, first, second)
    repository = SqlAlchemyTransactionRepository(sqlite_store.sessions)

    empty_page = exercise_call(
        repository.list_transactions,
        offset=2,
        limit=None,
        user_id=None,
        status=None,
    )
    assert empty_page == ()


@pytest.mark.parametrize(
    ("user_id", "status", "expected_ids"),
    [
        ("selected", None, (1, 3)),
        (None, "declined", (1, 2)),
        ("selected", "declined", (1,)),
    ],
)
@pytest.mark.student_exercise
def test_repository_list_applies_each_filter_independently_and_together(
    sqlite_store: SqliteStore,
    user_id: str | None,
    status: TransactionStatus | None,
    expected_ids: tuple[int, ...],
) -> None:
    selected = make_transaction(1, user_id="selected", status="declined")
    wrong_user = make_transaction(2, user_id="other", status="declined")
    wrong_status = make_transaction(3, user_id="selected", status="approved")
    seed_transactions(sqlite_store.sessions, selected, wrong_user, wrong_status)
    repository = SqlAlchemyTransactionRepository(sqlite_store.sessions)

    result = exercise_call(
        repository.list_transactions,
        offset=0,
        limit=100,
        user_id=user_id,
        status=status,
    )

    by_id = {
        transaction.id.int: transaction for transaction in (selected, wrong_user, wrong_status)
    }
    assert result == tuple(by_id[index] for index in expected_ids)


@pytest.mark.student_exercise
def test_duplicate_insert_is_atomic_rolls_back_closes_and_keeps_later_sessions_usable(
    sqlite_store: SqliteStore,
) -> None:
    existing = make_transaction(1, amount="10.00")
    seed_transactions(sqlite_store.sessions, existing)
    sessions = tracking_factory(sqlite_store.engine)
    repository = SqlAlchemyTransactionRepository(sessions)

    with pytest.raises(DuplicateTransactionError):
        exercise_call(repository.create_transaction, make_transaction(1, amount="99.99"))

    assert load_transactions_directly(sqlite_store.sessions) == (existing,)
    assert len(TrackingSession.instances) == 1
    assert TrackingSession.instances[0].rollback_count >= 1
    assert TrackingSession.instances[0].close_count >= 1
    with sqlite_store.sessions() as later_session:
        assert later_session.scalar(select(func.count()).select_from(TransactionRow)) == 1


@pytest.mark.student_exercise
def test_non_duplicate_integrity_errors_propagate_by_identity_and_still_clean_up() -> None:
    original = IntegrityError(
        "INSERT INTO transactions (...) VALUES (...) ",
        {},
        RuntimeError("unrelated check constraint"),
    )
    session = FailingSession(original, operation="write")
    repository = SqlAlchemyTransactionRepository(cast(Any, FailingSessionFactory(session)))

    with pytest.raises(IntegrityError) as caught:
        exercise_call(repository.create_transaction, make_transaction(1))

    assert caught.value is original
    assert session.rollback_count == 1
    assert session.close_count == 1


@pytest.mark.parametrize(
    ("operation", "invoke"),
    [
        (
            "write",
            lambda repository, transaction: repository.create_transaction(transaction),
        ),
        (
            "get",
            lambda repository, transaction: repository.get_transaction(transaction.id),
        ),
        (
            "list",
            lambda repository, _transaction: repository.list_transactions(
                offset=0,
                limit=10,
                user_id=None,
                status=None,
            ),
        ),
    ],
)
@pytest.mark.student_exercise
def test_repository_propagates_original_failures_when_rollback_and_close_also_fail(
    operation: str,
    invoke: Any,
) -> None:
    original = RuntimeError(f"original-{operation}-failure")
    session = FailingSession(original, operation=operation)
    factory = FailingSessionFactory(session)
    repository = SqlAlchemyTransactionRepository(cast(Any, factory))
    transaction = make_transaction(1)

    with pytest.raises(RuntimeError) as caught:
        exercise_call(invoke, repository, transaction)

    assert caught.value is original
    assert session.rollback_count == 1
    assert session.close_count == 1
