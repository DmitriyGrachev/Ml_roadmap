from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from roadmap_tools import exercise_call

from . import starter


def record(
    transaction_id: str,
    amount: str,
    currency: str,
    timestamp: datetime,
) -> object:
    return starter.TransactionRecord(
        id=transaction_id,
        user_id="user-1",
        amount=Decimal(amount),
        currency=currency,
        timestamp=timestamp,
    )


def test_daily_totals_filter_utc_day_aggregate_in_sql_and_sort_by_currency(
    tmp_path: Path,
) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'totals.db'}")
    starter.Base.metadata.create_all(engine)
    statements: list[str] = []

    def capture_sql(
        _connection: Connection,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", capture_sql)
    try:
        with Session(engine) as session:
            session.add_all(
                [
                    record("usd-1", "10.00", "USD", datetime(2026, 9, 19, 0, 0, tzinfo=UTC)),
                    record("usd-2", "2.50", "USD", datetime(2026, 9, 19, 23, 59, tzinfo=UTC)),
                    record("eur", "3.25", "EUR", datetime(2026, 9, 19, 8, 30, tzinfo=UTC)),
                    record("gbp", "4.75", "GBP", datetime(2026, 9, 19, 12, 0, tzinfo=UTC)),
                    record(
                        "previous",
                        "100.00",
                        "GBP",
                        datetime(2026, 9, 18, 23, 59, tzinfo=UTC),
                    ),
                    record("next", "200.00", "EUR", datetime(2026, 9, 20, 0, 0, tzinfo=UTC)),
                ]
            )
            session.commit()
            statements.clear()

            totals = exercise_call(starter.daily_currency_totals, session, date(2026, 9, 19))

        assert totals == [
            starter.CurrencyTotal(currency="EUR", total=Decimal("3.25")),
            starter.CurrencyTotal(currency="GBP", total=Decimal("4.75")),
            starter.CurrencyTotal(currency="USD", total=Decimal("12.50")),
        ]
        selects = [sql.upper() for sql in statements if sql.lstrip().upper().startswith("SELECT")]
        assert len(selects) == 1
        emitted_sql = selects[0]
        assert "SUM(" in emitted_sql
        assert "GROUP BY" in emitted_sql
        assert "ORDER BY" in emitted_sql
        assert "WHERE" in emitted_sql
    finally:
        event.remove(engine, "before_cursor_execute", capture_sql)
        engine.dispose()


def test_currency_total_is_immutable() -> None:
    total = starter.CurrencyTotal(currency="USD", total=Decimal("1.00"))

    with pytest.raises(FrozenInstanceError):
        total.total = Decimal("2.00")  # type: ignore[misc]
