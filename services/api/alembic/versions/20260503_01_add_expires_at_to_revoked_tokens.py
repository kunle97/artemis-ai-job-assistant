"""Add expires_at column to revoked_tokens for cleanup support."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260503_01"
down_revision: Union[str, None] = "20260502_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable expires_at column to revoked_tokens."""
    op.add_column(
        "revoked_tokens",
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Remove expires_at column from revoked_tokens."""
    op.drop_column("revoked_tokens", "expires_at")
