import os
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from roadmap_tools import exercise_call  # type: ignore[import-untyped]

from . import starter

POSTGRES_SKIP = "Set ROADMAP_POSTGRES_URL and run: docker compose up -d postgres"


@pytest.mark.postgres
def test_postgres_preserves_decimal_timezone_and_daily_aggregation() -> None:
    database_url = os.environ.get("ROADMAP_POSTGRES_URL")
    if database_url is None:
        pytest.skip(POSTGRES_SKIP)

    engine = create_engine(database_url)
    schema = f"roadmap_{uuid4().hex}"
    with engine.begin() as connection:
        connection.execute(CreateSchema(schema))

    try:
        with engine.connect().execution_options(schema_translate_map={None: schema}) as connection:
            transaction = connection.begin()
            try:
                connection.execute(text("SET TIME ZONE 'UTC'"))
                starter.Base.metadata.create_all(connection)
                with Session(connection, expire_on_commit=False) as session:
                    original = starter.TransactionRecord(
                        id="postgres-round-trip",
                        user_id="user-postgres",
                        amount=Decimal("1234.56"),
                        currency="EUR",
                        timestamp=datetime(
                            2026, 9, 19, 13, 30, tzinfo=timezone(timedelta(hours=3))
                        ),
                    )
                    session.add(original)
                    session.flush()
                    session.expire_all()

                    loaded = session.scalar(
                        select(starter.TransactionRecord).where(
                            starter.TransactionRecord.id == "postgres-round-trip"
                        )
                    )
                    assert loaded is not None
                    assert loaded.amount == Decimal("1234.56")
                    assert isinstance(loaded.amount, Decimal)
                    assert loaded.timestamp == datetime(2026, 9, 19, 10, 30, tzinfo=UTC)
                    assert loaded.timestamp.utcoffset() == timedelta(0)

                    totals = exercise_call(
                        starter.daily_currency_totals, session, date(2026, 9, 19)
                    )
                    assert totals == [
                        starter.CurrencyTotal(currency="EUR", total=Decimal("1234.56"))
                    ]
            finally:
                transaction.rollback()
    finally:
        with engine.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        engine.dispose()
