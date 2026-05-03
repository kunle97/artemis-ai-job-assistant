"""Add manual review gate fields to applications and auto_submit to candidate_profiles."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260503_05"
down_revision: Union[str, None] = "20260503_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_authorized_to_submit and manual_review_required to applications; add auto_submit to candidate_profiles."""
    op.add_column(
        "applications",
        sa.Column(
            "is_authorized_to_submit",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "applications",
        sa.Column(
            "manual_review_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "candidate_profiles",
        sa.Column(
            "auto_submit",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    """Remove manual review gate fields."""
    op.drop_column("candidate_profiles", "auto_submit")
    op.drop_column("applications", "manual_review_required")
    op.drop_column("applications", "is_authorized_to_submit")
