"""Student boundaries: orchestrate your document migrations, not the latency demo."""

from pathlib import Path


def upgrade_database(database: Path) -> None:
    """Upgrade the given SQLite file to student_migrations head using Alembic."""
    raise NotImplementedError("run the student's document upgrade through Alembic")


def downgrade_database(database: Path) -> None:
    """Downgrade the given SQLite file to student revision 0001 using Alembic."""
    raise NotImplementedError("run the student's data-preserving document downgrade")
