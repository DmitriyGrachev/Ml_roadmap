"""Independent document transfer; author latency revisions cannot satisfy these checks."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

pytest.importorskip(
    "alembic", reason="Install optional migrations group: uv sync --group migrations"
)

from alembic import command
from sqlalchemy.engine import URL

from roadmap_tools.exercise import exercise_call

from .demo import config_for
from .starter import downgrade_database, upgrade_database

pytestmark = pytest.mark.student_exercise
ROWS = [(1, "empty", ""), (2, "unicode", "ёж🙂"), (7, "multiline", "line\n")]


@pytest.fixture
def populated(tmp_path: Path) -> Path:
    database = tmp_path / "documents.sqlite"
    url = URL.create("sqlite", database=str(database)).render_as_string(hide_password=False)
    command.upgrade(config_for(url, "student_migrations"), "0001")
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executemany("INSERT INTO documents VALUES(?,?,?)", ROWS)
    return database


def test_backfill_preserves_content_and_enforces_new_writes(populated: Path) -> None:
    exercise_call(upgrade_database, populated)
    with closing(sqlite3.connect(populated)) as connection, connection:
        assert connection.execute(
            "SELECT id,title,body,body_length FROM documents ORDER BY id"
        ).fetchall() == [
            (1, "empty", "", 0),
            (2, "unicode", "ёж🙂", 3),
            (7, "multiline", "line\n", 5),
        ]
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0002",)
        columns = {row[1]: row for row in connection.execute("PRAGMA table_info(documents)")}
        assert columns["body_length"][2].upper() == "INTEGER"
        assert columns["body_length"][3] == 1
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO documents VALUES(8,'bad','x',NULL)")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO documents VALUES(9,'bad','x',-1)")
        connection.execute("INSERT INTO documents VALUES(10,'new','abc',3)")
    exercise_call(downgrade_database, populated)
    with closing(sqlite3.connect(populated)) as connection, connection:
        assert connection.execute("SELECT * FROM documents ORDER BY id").fetchall() == [
            *ROWS,
            (10, "new", "abc"),
        ]
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0001",)
        assert "ix_documents_title" in {
            row[1] for row in connection.execute("PRAGMA index_list(documents)")
        }


def test_repeated_targets_and_roundtrip_are_safe(populated: Path) -> None:
    exercise_call(upgrade_database, populated)
    exercise_call(upgrade_database, populated)
    exercise_call(downgrade_database, populated)
    exercise_call(downgrade_database, populated)
    exercise_call(upgrade_database, populated)
    with closing(sqlite3.connect(populated)) as connection, connection:
        assert connection.execute(
            "SELECT id,body_length FROM documents ORDER BY id"
        ).fetchall() == [
            (1, 0),
            (2, 3),
            (7, 5),
        ]
        assert (
            connection.execute("SELECT id,title,body FROM documents ORDER BY id").fetchall() == ROWS
        )
