"""Create application_scores table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260506_01"
down_revision: Union[str, None] = "20260505_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create application_scores table for job fit scoring results."""
    op.create_table(
        "application_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_fit", sa.Float(), nullable=True),
        sa.Column("seniority_match", sa.Float(), nullable=True),
        sa.Column("location_match", sa.Float(), nullable=True),
        sa.Column("global_score", sa.Float(), nullable=True),
        sa.Column("skills_gap_summary", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id", name="uq_application_scores_application_id"),
    )
    op.create_index(
        op.f("ix_application_scores_application_id"),
        "application_scores",
        ["application_id"],
        unique=True,
    )


def downgrade() -> None:
    """Drop application_scores table."""
    op.drop_index(op.f("ix_application_scores_application_id"), table_name="application_scores")
    op.drop_table("application_scores")
