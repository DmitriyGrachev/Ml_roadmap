"""Actual Alembic upgrade/backfill/downgrade against populated temporary SQLite."""

import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip(
    "alembic", reason="Install optional migrations group: uv sync --group migrations"
)

from alembic.operations import Operations
from sqlalchemy import Column
from sqlalchemy.exc import IntegrityError

from . import demo
from .demo import downgrade, upgrade


def test_populated_upgrade_backfill_new_write_and_downgrade_preserve_data(tmp_path: Path) -> None:
    database = tmp_path / "latency.sqlite"
    upgrade(database, "0001")
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executemany(
            "INSERT INTO prediction_jobs(id, model_name, latency_millis) VALUES(?,?,?)",
            [(1, "tiny-v1", 1250), (2, "old-v2", 0), (3, "café-v1", 999)],
        )
    upgrade(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        assert connection.execute(
            "SELECT id, model_name, latency_millis, latency_seconds "
            "FROM prediction_jobs ORDER BY id"
        ).fetchall() == [
            (1, "tiny-v1", 1250, 1.25),
            (2, "old-v2", 0, 0.0),
            (3, "café-v1", 999, 0.999),
        ]
        connection.execute("INSERT INTO prediction_jobs VALUES(4,'new-v3',250,0.25)")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO prediction_jobs VALUES(5,'missing',1,NULL)")
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0002",)
    downgrade(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        assert connection.execute("SELECT * FROM prediction_jobs ORDER BY id").fetchall() == [
            (1, "tiny-v1", 1250),
            (2, "old-v2", 0),
            (3, "café-v1", 999),
            (4, "new-v3", 250),
        ]
        assert [row[1] for row in connection.execute("PRAGMA table_info(prediction_jobs)")] == [
            "id",
            "model_name",
            "latency_millis",
        ]
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0001",)
    upgrade(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        assert connection.execute(
            "SELECT latency_seconds FROM prediction_jobs WHERE id=4"
        ).fetchone() == (0.25,)


def test_revision_one_rejects_invalid_write_without_losing_prior_data(tmp_path: Path) -> None:
    database = tmp_path / "failure.sqlite"
    upgrade(database, "0001")
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("INSERT INTO prediction_jobs VALUES(1,'valid',10)")
    with (
        closing(sqlite3.connect(database)) as connection,
        connection,
        pytest.raises(sqlite3.IntegrityError),
    ):
        connection.execute("INSERT INTO prediction_jobs VALUES(2,'negative',-1)")
    upgrade(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        assert connection.execute("SELECT id, latency_seconds FROM prediction_jobs").fetchall() == [
            (1, 0.01),
        ]


def test_backfill_validation_fails_before_schema_change_and_can_be_retried(tmp_path: Path) -> None:
    database = tmp_path / "legacy-corruption.sqlite"
    upgrade(database, "0001")
    with closing(sqlite3.connect(database)) as connection, connection:
        # Simulate legacy corruption from an earlier writer bypassing CHECK constraints.
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute("INSERT INTO prediction_jobs VALUES(1,'legacy',-5)")
    with pytest.raises((ValueError, IntegrityError), match=r"negative|CHECK"):
        upgrade(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        assert connection.execute("SELECT * FROM prediction_jobs").fetchall() == [(1, "legacy", -5)]
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0001",)
        assert len(connection.execute("PRAGMA table_info(prediction_jobs)").fetchall()) == 3
        connection.execute("UPDATE prediction_jobs SET latency_millis=5 WHERE id=1")
    upgrade(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        assert connection.execute("SELECT latency_seconds FROM prediction_jobs").fetchone() == (
            0.005,
        )


def test_failure_after_real_ddl_rolls_back_schema_and_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "ddl-failure.sqlite"
    upgrade(database, "0001")
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("INSERT INTO prediction_jobs VALUES(1,'preserved',1250)")
    original = Operations.add_column

    def add_then_fail(
        operation: Operations, table: str, column: Column[Any], *args: Any, **kwargs: Any
    ) -> None:
        original(operation, table, column, *args, **kwargs)
        raise RuntimeError("injected after real ADD COLUMN")

    with monkeypatch.context() as patch:
        patch.setattr(Operations, "add_column", add_then_fail)
        with pytest.raises(RuntimeError, match="injected after real ADD COLUMN"):
            upgrade(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        assert connection.execute("SELECT * FROM prediction_jobs").fetchall() == [
            (1, "preserved", 1250),
        ]
        assert [row[1] for row in connection.execute("PRAGMA table_info(prediction_jobs)")] == [
            "id",
            "model_name",
            "latency_millis",
        ]
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0001",)
    upgrade(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        assert connection.execute("SELECT latency_seconds FROM prediction_jobs").fetchone() == (
            1.25,
        )


@pytest.mark.parametrize("fail_before_downgrade", [False, True])
def test_demo_closes_raw_connections_before_temporary_directory_cleanup(
    monkeypatch: pytest.MonkeyPatch, fail_before_downgrade: bool
) -> None:
    connections: list[sqlite3.Connection] = []
    real_connect = sqlite3.connect
    real_temporary_directory = tempfile.TemporaryDirectory

    def connect(database: Path) -> sqlite3.Connection:
        connection = real_connect(database)
        connections.append(connection)
        return connection

    @contextmanager
    def checked_temporary_directory(*args: Any, **kwargs: Any) -> Iterator[str]:
        with real_temporary_directory(*args, **kwargs) as directory:
            try:
                yield directory
            finally:
                # Retain strong references: garbage collection cannot hide leaked handles.
                assert connections
                for connection in connections:
                    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
                        connection.execute("SELECT 1")

    def fail_downgrade(database: Path, revision: str = "0001") -> None:
        raise RuntimeError("injected before downgrade")

    monkeypatch.setattr(sqlite3, "connect", connect)
    monkeypatch.setattr(tempfile, "TemporaryDirectory", checked_temporary_directory)
    monkeypatch.setattr("sys.argv", ["schema-migrations-demo"])
    if fail_before_downgrade:
        monkeypatch.setattr(demo, "downgrade", fail_downgrade)
        with pytest.raises(RuntimeError, match="injected before downgrade"):
            demo.main()
    else:
        demo.main()
