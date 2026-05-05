"""Widen applications.status column to support pipeline lifecycle values."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260505_01"
down_revision: Union[str, None] = "20260504_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Expand applications.status length from 50 to 100 chars."""
    op.alter_column(
        "applications",
        "status",
        existing_type=sa.String(length=50),
        type_=sa.String(length=100),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Shrink applications.status length from 100 back to 50 chars."""
    op.alter_column(
        "applications",
        "status",
        existing_type=sa.String(length=100),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
