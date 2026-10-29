"""Student revision: add, backfill and constrain body_length; preserve legacy data."""

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TODO: body_length = number of Unicode code points in body, not UTF-8 bytes.
    raise NotImplementedError("migrate populated documents to non-null nonnegative body_length")


def downgrade() -> None:
    # TODO: remove only the derived column; retain rows, IDs, original fields and title index.
    raise NotImplementedError("downgrade document schema without dropping original data")
