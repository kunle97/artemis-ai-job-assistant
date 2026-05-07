"""Normalize application_answer categories: ai_generated -> AI Generated.

Revision ID: 20260507_01
Revises: 20260506_02
Create Date: 2026-05-07 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260507_01'
down_revision = '20260506_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE application_answers SET category = 'AI Generated' WHERE category = 'ai_generated'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE application_answers SET category = 'ai_generated' WHERE category = 'AI Generated'"
    )
