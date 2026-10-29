"""Author Alembic example; all default writes use a temporary SQLite database."""

import argparse
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alembic.config import Config


def config_for(database_url: str, directory: str = "demo_migrations") -> "Config":
    """No working-directory or alembic.ini assumptions; URL may target test PostgreSQL."""
    from alembic.config import Config

    config = Config()
    config.set_main_option("script_location", str(Path(__file__).with_name(directory)))
    # ConfigParser treats percent signs specially, e.g. URL-encoded passwords/paths.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def upgrade(database: Path, revision: str = "head") -> None:
    from alembic import command
    from sqlalchemy.engine import URL

    url = URL.create("sqlite", database=str(database.resolve()))
    command.upgrade(config_for(url.render_as_string(hide_password=False)), revision)


def downgrade(database: Path, revision: str = "0001") -> None:
    from alembic import command
    from sqlalchemy.engine import URL

    url = URL.create("sqlite", database=str(database.resolve()))
    command.downgrade(config_for(url.render_as_string(hide_password=False)), revision)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", help="Optional disposable PostgreSQL/SQLite database URL")
    parser.add_argument("--revision", default="head")
    parser.add_argument("--downgrade", help="Explicit downgrade target for optional external URL")
    args = parser.parse_args()
    if args.database_url:
        from alembic import command

        config = config_for(args.database_url)
        if args.downgrade:
            command.downgrade(config, args.downgrade)
        else:
            command.upgrade(config, args.revision)
        return
    with tempfile.TemporaryDirectory(prefix="latency-migrations-") as temporary:
        database = Path(temporary) / "example.sqlite"
        upgrade(database, "0001")
        with closing(sqlite3.connect(database)) as connection, connection:
            connection.executemany(
                "INSERT INTO prediction_jobs VALUES(?,?,?)",
                [(1, "tiny-v1", 1250), (2, "tiny-v2", 0)],
            )
        upgrade(database)
        with closing(sqlite3.connect(database)) as connection, connection:
            print("after upgrade:", connection.execute("SELECT * FROM prediction_jobs").fetchall())
        downgrade(database)
        with closing(sqlite3.connect(database)) as connection, connection:
            print(
                "after downgrade:", connection.execute("SELECT * FROM prediction_jobs").fetchall()
            )


if __name__ == "__main__":
    main()
