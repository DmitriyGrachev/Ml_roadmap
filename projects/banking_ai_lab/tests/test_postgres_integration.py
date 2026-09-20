"""Opt-in Stage 5 PostgreSQL semantics and API/database integration contracts."""

from __future__ import annotations

import os
import time
import warnings
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast
from uuid import UUID, uuid4

import pytest
from banking_ai_lab.app import create_app
from banking_ai_lab.domain import Transaction
from banking_ai_lab.persistence import (
    Base,
    SqlAlchemyTransactionRepository,
    TransactionRow,
    create_schema,
    create_session_factory,
)
from banking_ai_lab.service import TransactionService
from sqlalchemy import Engine, create_engine, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from starlette.exceptions import StarletteDeprecationWarning

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=StarletteDeprecationWarning)
    warnings.filterwarnings(
        "ignore",
        message="The anyio.abc.BlockingPortal alias is deprecated.*",
        category=DeprecationWarning,
    )
    from starlette.testclient import TestClient

from roadmap_tools import exercise_call

pytestmark = pytest.mark.postgres

POSTGRES_ENVIRONMENT = "ROADMAP_POSTGRES_URL"
POSTGRES_SKIP_REASON = (
    "Set ROADMAP_POSTGRES_URL after following "
    "projects/banking_ai_lab/stages/05_postgresql/README.md"
)
CONNECT_ATTEMPTS = 3
CONNECT_TIMEOUT_SECONDS = 2


@dataclass(frozen=True)
class PostgresStore:
    engine: Engine
    sessions: sessionmaker[Session]
    schema: str


def make_transaction(index: int, *, amount: str = "10.25") -> Transaction:
    return Transaction.model_validate(
        {
            "id": UUID(int=index),
            "user_id": f"user-{index:04d}",
            "amount": Decimal(amount),
            "currency": "EUR",
            "merchant": f"Merchant {index}",
            "category": "groceries",
            "timestamp": datetime(2025, 1, index, 10, tzinfo=UTC),
            "status": "approved",
            "is_fraud": False,
        }
    )


def request_json(transaction: Transaction) -> dict[str, object]:
    return {
        "id": str(transaction.id),
        "user_id": transaction.user_id,
        "amount": str(transaction.amount),
        "currency": transaction.currency,
        "merchant": transaction.merchant,
        "category": transaction.category,
        "timestamp": transaction.timestamp.isoformat().replace("+00:00", "Z"),
        "status": transaction.status,
        "is_fraud": transaction.is_fraud,
    }


def connect_with_bounded_retries(database_url: str) -> Engine:
    engine = create_engine(
        database_url,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
        pool_pre_ping=True,
    )
    last_error: BaseException | None = None
    for attempt in range(CONNECT_ATTEMPTS):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return engine
        except (SQLAlchemyError, OSError) as exc:
            last_error = exc
            if attempt + 1 < CONNECT_ATTEMPTS:
                time.sleep(0.2)
    engine.dispose()
    pytest.fail(
        f"{POSTGRES_ENVIRONMENT} is configured but unreachable after "
        f"{CONNECT_ATTEMPTS} attempts: {type(last_error).__name__}"
    )


@pytest.fixture
def postgres_store() -> Iterator[PostgresStore]:
    database_url = os.environ.get(POSTGRES_ENVIRONMENT)
    if database_url is None:
        pytest.skip(POSTGRES_SKIP_REASON)

    administrative_engine = connect_with_bounded_retries(database_url)
    schema = f"banking_ai_lab_test_{uuid4().hex}"
    schema_created = False
    isolated_engine = administrative_engine.execution_options(schema_translate_map={None: schema})
    try:
        with administrative_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        schema_created = True
        create_schema(isolated_engine)
        yield PostgresStore(
            engine=isolated_engine,
            sessions=create_session_factory(isolated_engine),
            schema=schema,
        )
    finally:
        try:
            if schema_created:
                try:
                    Base.metadata.drop_all(isolated_engine)
                finally:
                    with administrative_engine.begin() as connection:
                        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        finally:
            administrative_engine.dispose()


def seed_transaction(store: PostgresStore, transaction: Transaction) -> None:
    with store.sessions() as session:
        session.add(TransactionRow.from_transaction(transaction))
        session.commit()


def test_postgresql_uses_numeric_and_timestamptz(postgres_store: PostgresStore) -> None:
    with postgres_store.engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT column_name, data_type "
                "FROM information_schema.columns "
                "WHERE table_schema = :schema AND table_name = :table"
            ),
            {"schema": postgres_store.schema, "table": TransactionRow.__tablename__},
        ).mappings()
        columns = {row["column_name"]: row for row in rows}

    assert columns["amount"]["data_type"] == "numeric"
    assert columns["timestamp"]["data_type"] == "timestamp with time zone"


@pytest.mark.student_exercise
def test_postgresql_api_create_reaches_the_isolated_database(
    postgres_store: PostgresStore,
) -> None:
    transaction = make_transaction(1, amount="0.10")
    repository = SqlAlchemyTransactionRepository(postgres_store.sessions)
    app = create_app(TransactionService(repository))

    with TestClient(app) as client:
        response = exercise_call(client.post, "/api/transactions", json=request_json(transaction))

    assert response.status_code == 201
    assert response.json() == request_json(transaction)
    with postgres_store.sessions() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(TransactionRow)
                .where(TransactionRow.id == transaction.id)
            )
            == 1
        )


@pytest.mark.student_exercise
def test_postgresql_api_get_restores_exact_decimal_and_utc(
    postgres_store: PostgresStore,
) -> None:
    transaction = make_transaction(2, amount="9876543210.12")
    seed_transaction(postgres_store, transaction)
    repository = SqlAlchemyTransactionRepository(postgres_store.sessions)
    app = create_app(TransactionService(repository))

    with TestClient(app) as client:
        response = exercise_call(client.get, f"/api/transactions/{transaction.id}")

    assert response.status_code == 200
    assert response.json() == request_json(transaction)
    loaded_timestamp = datetime.fromisoformat(
        cast(str, response.json()["timestamp"]).replace("Z", "+00:00")
    )
    assert loaded_timestamp.tzinfo is not None
