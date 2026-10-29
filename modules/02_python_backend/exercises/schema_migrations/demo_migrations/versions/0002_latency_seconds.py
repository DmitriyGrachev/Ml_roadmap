"""Expand, backfill, constrain; downgrade preserves the original latency column."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    invalid = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT COUNT(*) FROM prediction_jobs "
                "WHERE latency_millis < 0 OR latency_millis IS NULL"
            )
        )
        .scalar_one()
    )
    if invalid:
        raise ValueError("legacy negative or missing latency; repair before migration")
    op.add_column("prediction_jobs", sa.Column("latency_seconds", sa.Float(), nullable=True))
    op.execute(sa.text("UPDATE prediction_jobs SET latency_seconds = latency_millis / 1000.0"))
    with op.batch_alter_table("prediction_jobs") as batch:
        batch.alter_column("latency_seconds", existing_type=sa.Float(), nullable=False)
        batch.create_check_constraint("ck_latency_seconds_nonnegative", "latency_seconds >= 0")


def downgrade() -> None:
    with op.batch_alter_table("prediction_jobs") as batch:
        batch.drop_constraint("ck_latency_seconds_nonnegative", type_="check")
        batch.drop_column("latency_seconds")
