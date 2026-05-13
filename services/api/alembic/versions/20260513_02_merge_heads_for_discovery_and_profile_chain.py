"""Merge discovery and profile migration heads.

Revision ID: 20260513_02
Revises: 20260510_01, 20260513_01
Create Date: 2026-05-13 10:00:00.000000

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "20260513_02"
down_revision: Union[str, Sequence[str], None] = ("20260510_01", "20260513_01")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge branches without schema changes."""


def downgrade() -> None:
    """No-op downgrade for merge revision."""
