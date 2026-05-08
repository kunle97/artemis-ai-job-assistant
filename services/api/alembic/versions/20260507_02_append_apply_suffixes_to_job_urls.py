"""Append required source-specific suffixes to persisted job apply URLs.

Revision ID: 20260507_02
Revises: 20260507_01
Create Date: 2026-05-07 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260507_02"
down_revision = "20260507_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Append /apply for Lever and /application for Ashby job apply URLs."""
    op.execute(
        """
        UPDATE jobs
        SET apply_url = CASE
            WHEN RIGHT(apply_url, 1) = '/' THEN apply_url || 'apply'
            ELSE apply_url || '/apply'
        END
        WHERE source = 'lever'
          AND apply_url IS NOT NULL
          AND apply_url <> ''
          AND apply_url !~ '/apply/?$';
        """
    )

    op.execute(
        """
        UPDATE jobs
        SET apply_url = CASE
            WHEN RIGHT(apply_url, 1) = '/' THEN apply_url || 'application'
            ELSE apply_url || '/application'
        END
        WHERE source = 'ashby'
          AND apply_url IS NOT NULL
          AND apply_url <> ''
          AND apply_url !~ '/application/?$';
        """
    )


def downgrade() -> None:
    """Remove appended suffixes from Lever and Ashby job apply URLs."""
    op.execute(
        """
        UPDATE jobs
        SET apply_url = REGEXP_REPLACE(apply_url, '/apply/?$', '')
        WHERE source = 'lever'
          AND apply_url IS NOT NULL
          AND apply_url ~ '/apply/?$';
        """
    )

    op.execute(
        """
        UPDATE jobs
        SET apply_url = REGEXP_REPLACE(apply_url, '/application/?$', '')
        WHERE source = 'ashby'
          AND apply_url IS NOT NULL
          AND apply_url ~ '/application/?$';
        """
    )
