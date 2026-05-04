"""Create job_user_feed table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260504_01"
down_revision: Union[str, None] = "1cf798acfa49"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create per-user job feed tracking table."""
    op.create_table(
        "job_user_feed",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("new", "seen", "saved", "dismissed", name="job_feed_status", native_enum=False),
            nullable=False,
            server_default="new",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id", name="uq_job_user_feed_user_job"),
    )
    op.create_index(op.f("ix_job_user_feed_user_id"), "job_user_feed", ["user_id"], unique=False)
    op.create_index(op.f("ix_job_user_feed_job_id"), "job_user_feed", ["job_id"], unique=False)


def downgrade() -> None:
    """Drop per-user job feed tracking table."""
    op.drop_index(op.f("ix_job_user_feed_job_id"), table_name="job_user_feed")
    op.drop_index(op.f("ix_job_user_feed_user_id"), table_name="job_user_feed")
    op.drop_table("job_user_feed")