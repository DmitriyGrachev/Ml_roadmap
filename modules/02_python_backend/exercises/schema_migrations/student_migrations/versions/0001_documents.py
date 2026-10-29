"""Given legacy schema: the learner must migrate real existing document rows."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
    )
    op.create_index("ix_documents_title", "documents", ["title"])


def downgrade() -> None:
    op.drop_index("ix_documents_title", table_name="documents")
    op.drop_table("documents")
