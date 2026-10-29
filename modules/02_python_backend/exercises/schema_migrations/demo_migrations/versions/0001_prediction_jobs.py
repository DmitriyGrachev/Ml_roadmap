"""Baseline: original data remains the authority during the expand phase."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prediction_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("latency_millis", sa.Integer(), nullable=False),
        sa.CheckConstraint("latency_millis >= 0", name="ck_latency_millis_nonnegative"),
    )


def downgrade() -> None:
    op.drop_table("prediction_jobs")
