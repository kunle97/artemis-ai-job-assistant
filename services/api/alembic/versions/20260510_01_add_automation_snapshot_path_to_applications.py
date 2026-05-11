"""Add automation_snapshot_path to applications."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260510_01"
down_revision: Union[str, None] = "20260509_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Persist the latest automation snapshot reference on applications."""
    op.add_column(
        "applications",
        sa.Column("automation_snapshot_path", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Drop the stored automation snapshot reference from applications."""
    op.drop_column("applications", "automation_snapshot_path")