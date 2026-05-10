"""Add relocation preference and desired start date fields to candidate profiles.

Revision ID: 20260509_01
Revises: 20260507_02
Create Date: 2026-05-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260509_01"
down_revision = "20260507_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add relocation and desired-start-date profile columns."""
    op.add_column(
        "candidate_profiles",
        sa.Column("willing_to_relocate", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "candidate_profiles",
        sa.Column("relocation_destinations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "candidate_profiles",
        sa.Column("desired_start_date", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Remove relocation and desired-start-date profile columns."""
    op.drop_column("candidate_profiles", "desired_start_date")
    op.drop_column("candidate_profiles", "relocation_destinations")
    op.drop_column("candidate_profiles", "willing_to_relocate")
