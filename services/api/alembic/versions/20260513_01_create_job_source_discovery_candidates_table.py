"""Create job_source_discovery_candidates table.

Revision ID: 20260513_01
Revises: 20260506_02
Create Date: 2026-05-13 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260513_01"
down_revision = "20260506_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_source_discovery_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_channel", sa.String(length=40), nullable=False),
        sa.Column("input_url", sa.Text(), nullable=False),
        sa.Column("discovered_url", sa.Text(), nullable=False),
        sa.Column("detected_provider", sa.String(length=50), nullable=False),
        sa.Column("raw_candidate_value", sa.String(length=255), nullable=True),
        sa.Column("normalized_token", sa.String(length=255), nullable=True),
        sa.Column("extraction_timestamp", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_job_source_discovery_candidates_run_id"),
        "job_source_discovery_candidates",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_job_source_discovery_candidates_run_id"),
        table_name="job_source_discovery_candidates",
    )
    op.drop_table("job_source_discovery_candidates")
