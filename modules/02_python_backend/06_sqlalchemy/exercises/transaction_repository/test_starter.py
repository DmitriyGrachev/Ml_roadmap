from collections.abc import Iterator
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar, cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from roadmap_tools import exercise_call  # type: ignore[import-untyped]

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
) -> Iterator[tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession]]]:
    engine = create_engine(f"sqlite:///{tmp_path / 'transactions.db'}")
    starter.Base.metadata.create_all(engine)
    TrackingSession.created = []
    factory = sessionmaker(engine, class_=TrackingSession, expire_on_commit=False)
    typed_factory = cast(sessionmaker[Session], factory)
    yield starter.SqlAlchemyTransactionRepository(typed_factory), TrackingSession.created
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


def test_add_and_get_preserve_decimal_and_normalize_timestamp_to_utc(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession]],
) -> None:
    repo, sessions = repository
    original = transaction(
        "tx-round-trip",
        amount="19.99",
        timestamp=datetime(2026, 9, 19, 12, 15, tzinfo=timezone(timedelta(hours=2))),
    )

    exercise_call(repo.add, original)
    loaded = exercise_call(repo.get, "tx-round-trip")

    assert loaded is not None
    assert loaded.id == "tx-round-trip"
    assert loaded.amount == Decimal("19.99")
    assert isinstance(loaded.amount, Decimal)
    assert loaded.timestamp == datetime(2026, 9, 19, 10, 15, tzinfo=UTC)
    assert loaded.timestamp.utcoffset() == timedelta(0)
    assert sessions
    assert all(session.closed for session in sessions)


def test_get_unknown_id_returns_none_and_closes_session(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession]],
) -> None:
    repo, sessions = repository

    assert exercise_call(repo.get, "missing") is None
    assert len(sessions) == 1
    assert sessions[0].closed


def test_list_by_user_filters_and_orders_by_timestamp_then_id(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession]],
) -> None:
    repo, sessions = repository
    later = datetime(2026, 9, 19, 11, 0, tzinfo=UTC)
    earlier = datetime(2026, 9, 19, 9, 0, tzinfo=UTC)
    for record in [
        transaction("tx-b", timestamp=later),
        transaction("other", user_id="user-2", timestamp=earlier),
        transaction("tx-c", timestamp=earlier),
        transaction("tx-a", timestamp=earlier),
    ]:
        exercise_call(repo.add, record)

    records = exercise_call(repo.list_by_user, "user-1")

    assert [record.id for record in records] == ["tx-a", "tx-c", "tx-b"]
    assert all(record.user_id == "user-1" for record in records)
    assert all(session.closed for session in sessions)


def test_add_rolls_back_integrity_error_closes_session_and_keeps_prior_data(
    repository: tuple[starter.SqlAlchemyTransactionRepository, list[TrackingSession]],
) -> None:
    repo, sessions = repository
    exercise_call(repo.add, transaction("duplicate", amount="4.20"))

    with pytest.raises(IntegrityError):
        exercise_call(repo.add, transaction("duplicate", amount="99.00"))

    failed_session = sessions[-1]
    assert failed_session.rollback_count >= 1
    assert failed_session.closed
    loaded = exercise_call(repo.get, "duplicate")
    assert loaded is not None
    assert loaded.amount == Decimal("4.20")


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
