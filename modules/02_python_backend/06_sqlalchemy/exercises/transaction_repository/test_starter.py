from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar, cast

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from roadmap_tools import exercise_call

from . import starter


class TrackingSession(Session):
    """Expose lifecycle events without replacing SQLAlchemy behavior."""

    created: ClassVar[list["TrackingSession"]] = []
    closed = False
    rollback_count = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.created.append(self)

    def close(self) -> None:
        self.closed = True
        super().close()

    def rollback(self) -> None:
        self.rollback_count += 1
        super().rollback()


@pytest.fixture
def repository(
    tmp_path: Path,
) -> Iterator[tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession], Engine]]:
    engine = create_engine(f"sqlite:///{tmp_path / 'transactions.db'}")
    starter.Base.metadata.create_all(engine)
    TrackingSession.created = []
    factory = sessionmaker(engine, class_=TrackingSession, expire_on_commit=False)
    typed_factory = cast(sessionmaker[Session], factory)
    yield (
        starter.SqlAlchemyTransactionRepository(typed_factory),
        TrackingSession.created,
        engine,
    )
    engine.dispose()


def transaction(
    transaction_id: str,
    *,
    user_id: str = "user-1",
    amount: str = "12.50",
    currency: str = "USD",
    timestamp: datetime | None = None,
) -> starter.TransactionRecord:
    return starter.TransactionRecord(
        id=transaction_id,
        user_id=user_id,
        amount=Decimal(amount),
        currency=currency,
        timestamp=timestamp or datetime(2026, 9, 19, 10, 15, tzinfo=UTC),
    )


def seed(engine: Engine, *records: starter.TransactionRecord) -> None:
    with Session(engine) as session:
        session.add_all(records)
        session.commit()


class ReadFailure(RuntimeError):
    """Sentinel error raised from the real SQLAlchemy execution boundary."""


READ_FAILURE = ReadFailure("database read failed")


def raise_read_failure(
    _connection: Connection,
    _cursor: object,
    _statement: str,
    _parameters: object,
    _context: object,
    _executemany: bool,
) -> None:
    raise READ_FAILURE


def test_add_preserves_decimal_normalizes_timestamp_to_utc_and_closes_session(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession], Engine],
) -> None:
    repo, sessions, engine = repository
    original = transaction(
        "tx-round-trip",
        amount="19.99",
        timestamp=datetime(2026, 9, 19, 12, 15, tzinfo=timezone(timedelta(hours=2))),
    )

    exercise_call(repo.add, original)

    with Session(engine) as verification_session:
        loaded = verification_session.get(starter.TransactionRecord, "tx-round-trip")

    assert loaded is not None
    assert loaded.id == "tx-round-trip"
    assert loaded.amount == Decimal("19.99")
    assert isinstance(loaded.amount, Decimal)
    assert loaded.timestamp == datetime(2026, 9, 19, 10, 15, tzinfo=UTC)
    assert loaded.timestamp.utcoffset() == timedelta(0)
    assert len(sessions) == 1
    assert sessions[0].closed


def test_get_preserves_decimal_normalizes_timestamp_to_utc_and_closes_session(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession], Engine],
) -> None:
    repo, sessions, engine = repository
    seed(
        engine,
        transaction(
            "tx-round-trip",
            amount="19.99",
            timestamp=datetime(2026, 9, 19, 12, 15, tzinfo=timezone(timedelta(hours=2))),
        ),
    )

    loaded = exercise_call(repo.get, "tx-round-trip")

    assert loaded is not None
    assert loaded.id == "tx-round-trip"
    assert loaded.amount == Decimal("19.99")
    assert isinstance(loaded.amount, Decimal)
    assert loaded.timestamp == datetime(2026, 9, 19, 10, 15, tzinfo=UTC)
    assert loaded.timestamp.utcoffset() == timedelta(0)
    assert len(sessions) == 1
    assert sessions[0].closed


def test_get_unknown_id_returns_none_and_closes_session(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession], Engine],
) -> None:
    repo, sessions, _engine = repository

    assert exercise_call(repo.get, "missing") is None
    assert len(sessions) == 1
    assert sessions[0].closed


def test_list_by_user_filters_and_orders_by_timestamp_then_id(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession], Engine],
) -> None:
    repo, sessions, engine = repository
    later = datetime(2026, 9, 19, 11, 0, tzinfo=UTC)
    earlier = datetime(2026, 9, 19, 9, 0, tzinfo=UTC)
    seed(
        engine,
        transaction("tx-b", timestamp=later),
        transaction("other", user_id="user-2", timestamp=earlier),
        transaction("tx-c", timestamp=earlier),
        transaction("tx-a", timestamp=earlier),
    )

    records = exercise_call(repo.list_by_user, "user-1")

    assert [record.id for record in records] == ["tx-a", "tx-c", "tx-b"]
    assert all(record.user_id == "user-1" for record in records)
    assert all(session.closed for session in sessions)


def test_add_rolls_back_integrity_error_closes_session_and_keeps_prior_data(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession], Engine],
) -> None:
    repo, sessions, engine = repository
    seed(engine, transaction("duplicate", amount="4.20"))

    with pytest.raises(IntegrityError):
        exercise_call(repo.add, transaction("duplicate", amount="99.00"))

    failed_session = sessions[-1]
    assert failed_session.rollback_count >= 1
    assert failed_session.closed
    with Session(engine) as verification_session:
        loaded = verification_session.get(starter.TransactionRecord, "duplicate")
        assert loaded is not None
        assert loaded.amount == Decimal("4.20")


@pytest.mark.parametrize("operation", ["get", "list_by_user"])
def test_read_error_propagates_original_error_rolls_back_and_closes_session(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession], Engine],
    operation: str,
) -> None:
    repo, sessions, engine = repository
    seed(engine, transaction("existing"))
    operation_method: Callable[[str], object] = (
        repo.get if operation == "get" else repo.list_by_user
    )
    operation_argument = "existing" if operation == "get" else "user-1"
    event.listen(engine, "before_cursor_execute", raise_read_failure)
    try:
        with pytest.raises(ReadFailure, match="database read failed") as caught:
            exercise_call(operation_method, operation_argument)
    finally:
        event.remove(engine, "before_cursor_execute", raise_read_failure)

    assert caught.value is READ_FAILURE
    assert len(sessions) == 1
    assert sessions[0].rollback_count >= 1
    assert sessions[0].closed


@pytest.mark.parametrize(
    ("overrides", "expected_exception"),
    [
        ({"id": "  "}, ValueError),
        ({"user_id": "  "}, ValueError),
        ({"amount": "1.00"}, TypeError),
        ({"currency": "usd"}, ValueError),
        ({"currency": "US"}, ValueError),
        ({"timestamp": datetime(2026, 9, 19, 10, 15)}, ValueError),
    ],
    ids=[
        "blank-id",
        "blank-user",
        "non-decimal",
        "lowercase-currency",
        "short-currency",
        "naive-time",
    ],
)
def test_record_rejects_invalid_domain_values(
    overrides: dict[str, object], expected_exception: type[Exception]
) -> None:
    values: dict[str, object] = {
        "id": "tx-valid",
        "user_id": "user-1",
        "amount": Decimal("1.00"),
        "currency": "USD",
        "timestamp": datetime(2026, 9, 19, 10, 15, tzinfo=UTC),
    }
    values.update(overrides)

    with pytest.raises(expected_exception):
        starter.TransactionRecord(**values)
