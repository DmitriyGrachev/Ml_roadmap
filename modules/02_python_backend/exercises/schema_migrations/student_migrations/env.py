"""Online migration environment, including explicit transactional SQLite DDL."""

from sqlite3 import Connection as SQLiteConnection

from alembic import context
from sqlalchemy import engine_from_config, event, pool
from sqlalchemy.engine import Connection
from sqlalchemy.pool import ConnectionPoolEntry


def run_migrations() -> None:
    engine = engine_from_config(
        context.config.get_section(context.config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def disable_driver_transaction_control(
            dbapi_connection: SQLiteConnection, connection_record: ConnectionPoolEntry
        ) -> None:
            dbapi_connection.isolation_level = None

        @event.listens_for(engine, "begin")
        def explicit_begin(connection: Connection) -> None:
            connection.exec_driver_sql("BEGIN")

    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=None,
                transaction_per_migration=True,
                render_as_batch=engine.dialect.name == "sqlite",
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
